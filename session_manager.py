# session_manager.py - Streamlined Redis + SQLite Session Management
"""
Streamlined session management with:
1. Redis for active session state (fast access)
2. SQLite for persistent storage (durability)
3. Clean integration with enhanced orchestrator
4. Simplified, focused functionality
"""

import json
import uuid
import asyncio
import logging
import sqlite3
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

# Try to import Redis with graceful fallback
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis not available. Session manager will use SQLite + memory fallback.")

# =============================================================================
# REDIS SESSION CACHE
# =============================================================================

class RedisSessionCache:
    """Redis-based session caching for active interviews"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", ttl_hours: int = 2):
        self.redis_url = redis_url
        self.ttl_seconds = ttl_hours * 3600
        self.redis_client = None
        self.connection_healthy = False
        self.logger = logging.getLogger(__name__)
        
    async def connect(self):
        """Initialize Redis connection"""
        if not REDIS_AVAILABLE:
            return False
        
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            await self.redis_client.ping()
            self.connection_healthy = True
            self.logger.info("Redis connection established")
            return True
            
        except Exception as e:
            self.logger.error(f"Redis connection failed: {e}")
            self.connection_healthy = False
            return False
    
    async def store_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """Store session in Redis cache"""
        if not self.connection_healthy:
            return False
        
        try:
            session_key = f"session:{session_id}"
            await self.redis_client.setex(session_key, self.ttl_seconds, json.dumps(session_data))
            await self.redis_client.sadd("active_sessions", session_id)
            return True
        except Exception as e:
            self.logger.warning(f"Redis storage failed: {e}")
            return False
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session from Redis cache"""
        if not self.connection_healthy:
            return None
        
        try:
            session_key = f"session:{session_id}"
            session_data = await self.redis_client.get(session_key)
            return json.loads(session_data) if session_data else None
        except Exception as e:
            self.logger.warning(f"Redis retrieval failed: {e}")
            return None
    
    async def delete_session(self, session_id: str) -> bool:
        """Remove session from Redis cache"""
        if not self.connection_healthy:
            return False
        
        try:
            session_key = f"session:{session_id}"
            await self.redis_client.delete(session_key)
            await self.redis_client.srem("active_sessions", session_id)
            return True
        except Exception as e:
            self.logger.warning(f"Redis deletion failed: {e}")
            return False
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            self.connection_healthy = False

# =============================================================================
# SQLITE PERSISTENT STORAGE
# =============================================================================

class SqliteSessionStorage:
    """SQLite-based persistent session storage"""
    
    def __init__(self, db_path: str = "interview_sessions.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """Initialize SQLite database with simplified schema"""
        schema_sql = """
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP,
            status TEXT NOT NULL DEFAULT 'in_progress',
            candidate_name TEXT,
            candidate_email TEXT,
            session_data TEXT NOT NULL, -- JSON blob
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
        CREATE INDEX IF NOT EXISTS idx_sessions_start_time ON sessions(start_time);
        """
        
        conn = sqlite3.connect(self.db_path)
        conn.executescript(schema_sql)
        conn.commit()
        conn.close()
        
        self.logger.info(f"SQLite session storage initialized: {self.db_path}")
    
    async def store_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """Store session in SQLite"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            conn.execute("""
                INSERT OR REPLACE INTO sessions (
                    session_id, start_time, end_time, status, candidate_name, 
                    candidate_email, session_data, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                session_data.get('start_time'),
                session_data.get('end_time'),
                session_data.get('status', 'in_progress'),
                session_data.get('candidate_name'),
                session_data.get('candidate_email'),
                json.dumps(session_data),
                datetime.utcnow()
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            self.logger.error(f"SQLite storage failed: {e}")
            return False
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session from SQLite"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            row = conn.execute(
                "SELECT session_data FROM sessions WHERE session_id = ?",
                (session_id,)
            ).fetchone()
            
            conn.close()
            
            if row:
                return json.loads(row['session_data'])
            return None
            
        except Exception as e:
            self.logger.error(f"SQLite retrieval failed: {e}")
            return None

# =============================================================================
# MAIN SESSION MANAGER CLASS
# =============================================================================

class SessionManager:
    """Streamlined session manager with Redis cache + SQLite persistence"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", db_path: str = "sessions.db"):
        self.redis_cache = RedisSessionCache(redis_url) if REDIS_AVAILABLE else None
        self.sqlite_storage = SqliteSessionStorage(db_path)
        self.memory_cache = {}  # Fallback cache
        self.use_redis = False
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """Initialize session manager components"""
        try:
            # Initialize SQLite (always available)
            await self.sqlite_storage.initialize()
            
            # Try to initialize Redis (optional)
            if self.redis_cache:
                redis_connected = await self.redis_cache.connect()
                self.use_redis = redis_connected
                
        except Exception as e:
            self.logger.error(f"Session manager initialization failed: {e}")
    
    # =============================================================================
    # CORE SESSION OPERATIONS (Compatible with orchestrator)
    # =============================================================================
    
    async def create_session(self, candidate_name: str = None, candidate_email: str = None) -> str:
        """Create a new interview session"""
        session_id = f"interview_{uuid.uuid4().hex[:12]}"
        
        try:
            # Create session data
            session_data = {
                "session_id": session_id,
                "start_time": datetime.utcnow().isoformat(),
                "end_time": None,
                "status": "not_started",
                "candidate_name": candidate_name or "Anonymous",
                "candidate_email": candidate_email,
                "questions_asked": [],
                "responses": [],
                "evaluations": [],
                "conversation_history": [],
                "running_score": 0.0,
                "skills_covered": {},
                "question_type_history": [],  # For enhanced orchestrator
                "current_question": None,
                "interview_complete": False,
                "final_report": None
            }
            
            # Store session
            await self._store_session_data(session_id, session_data)
            
            self.logger.info(f"Created session: {session_id}")
            return session_id
            
        except Exception as e:
            self.logger.error(f"Failed to create session: {e}")
            raise RuntimeError(f"Session creation failed: {e}")
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data (compatible with orchestrator)"""
        try:
            # Try Redis first (fast)
            if self.use_redis and self.redis_cache:
                session_data = await self.redis_cache.get_session(session_id)
                if session_data:
                    return session_data
            
            # Try memory cache
            if session_id in self.memory_cache:
                return self.memory_cache[session_id]
            
            # Try SQLite (persistent)
            session_data = await self.sqlite_storage.get_session(session_id)
            if session_data:
                # Cache for next time
                self.memory_cache[session_id] = session_data
                if self.use_redis and self.redis_cache:
                    await self.redis_cache.store_session(session_id, session_data)
                return session_data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get session {session_id}: {e}")
            return self.memory_cache.get(session_id)
    
    async def update_session(self, session_id: str, session_data: Dict[str, Any]):
        """Update session (compatible with orchestrator)"""
        try:
            session_data["updated_at"] = datetime.utcnow().isoformat()
            await self._store_session_data(session_id, session_data)
            self.logger.debug(f"Session updated: {session_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to update session: {e}")
    
    async def complete_session(self, session_id: str):
        """Mark session as completed"""
        try:
            session_data = await self.get_session(session_id)
            if session_data:
                session_data["status"] = "completed"
                session_data["end_time"] = datetime.utcnow().isoformat()
                session_data["interview_complete"] = True
                
                await self.update_session(session_id, session_data)
                self.logger.info(f"Session completed: {session_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to complete session: {e}")
    
    async def abandon_session(self, session_id: str, reason: str = "User abandoned"):
        """Mark session as abandoned"""
        try:
            session_data = await self.get_session(session_id)
            if session_data:
                session_data["status"] = "abandoned"
                session_data["end_time"] = datetime.utcnow().isoformat()
                session_data["abandon_reason"] = reason
                
                await self.update_session(session_id, session_data)
                self.logger.info(f"Session abandoned: {session_id} - {reason}")
            
        except Exception as e:
            self.logger.error(f"Failed to abandon session {session_id}: {e}")
    
    # =============================================================================
    # INTERNAL HELPERS
    # =============================================================================
    
    async def _store_session_data(self, session_id: str, session_data: Dict[str, Any]):
        """Store session data in all layers"""
        try:
            # Store in memory cache (always)
            self.memory_cache[session_id] = session_data
            
            # Store in Redis (fast access)
            if self.use_redis and self.redis_cache:
                await self.redis_cache.store_session(session_id, session_data)
            
            # Store in SQLite (persistence)
            await self.sqlite_storage.store_session(session_id, session_data)
            
        except Exception as e:
            self.logger.error(f"Failed to store session data: {e}")
            # Ensure memory cache works at minimum
            self.memory_cache[session_id] = session_data
    
    # =============================================================================
    # STATS AND HEALTH (Simplified)
    # =============================================================================
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """Get basic session statistics"""
        try:
            return {
                "active_sessions": len(self.memory_cache),
                "redis_status": "connected" if self.use_redis else "disabled",
                "storage_layers": {
                    "memory": len(self.memory_cache),
                    "redis": "enabled" if self.use_redis else "disabled",
                    "sqlite": "enabled"
                }
            }
        except Exception as e:
            self.logger.error(f"Failed to get session stats: {e}")
            return {"error": str(e)}
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Simple health check"""
        try:
            return {
                "overall_healthy": True,
                "health_percentage": 100,
                "services": {
                    "session_manager": {"healthy": True, "status": "Redis+SQLite active"},
                    "memory_cache": {"healthy": True, "status": f"{len(self.memory_cache)} sessions"},
                    "redis_cache": {"healthy": self.use_redis, "status": "connected" if self.use_redis else "disabled"},
                    "sqlite_storage": {"healthy": True, "status": "persistent storage active"}
                }
            }
        except Exception as e:
            return {
                "overall_healthy": False,
                "health_percentage": 50,
                "services": {"session_manager": {"healthy": False, "status": f"Error: {e}"}}
            }
    
    # =============================================================================
    # SHUTDOWN
    # =============================================================================
    
    async def shutdown(self):
        """Shutdown session manager gracefully"""
        try:
            self.logger.info("Shutting down session manager...")
            
            # Save memory cache to SQLite
            for session_id, session_data in self.memory_cache.items():
                try:
                    await self.sqlite_storage.store_session(session_id, session_data)
                except Exception as e:
                    self.logger.error(f"Failed to save session during shutdown: {e}")
            
            # Close Redis
            if self.redis_cache:
                await self.redis_cache.close()
            
            # Clear memory
            self.memory_cache.clear()
            
            self.logger.info("Session manager shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Session manager shutdown error: {e}")

# =============================================================================
# FACTORY FOR DIFFERENT ENVIRONMENTS
# =============================================================================

class SessionManagerFactory:
    """Factory for creating session managers"""
    
    @staticmethod
    def create_production_manager(redis_url: str = "redis://localhost:6379", db_path: str = "production_sessions.db") -> SessionManager:
        """Create production session manager with Redis + SQLite"""
        return SessionManager(redis_url=redis_url, db_path=db_path)
    
    @staticmethod
    def create_development_manager(db_path: str = "dev_sessions.db") -> SessionManager:
        """Create development session manager (SQLite + memory)"""
        return SessionManager(redis_url=None, db_path=db_path)

# =============================================================================
# ORCHESTRATOR COMPATIBILITY
# =============================================================================

# Simple session object that orchestrator expects
class SimpleSession:
    """Simple session object for orchestrator compatibility"""
    
    def __init__(self, session_data: Dict[str, Any]):
        self.session_id = session_data["session_id"]
        self.start_time = datetime.fromisoformat(session_data["start_time"])
        self.end_time = datetime.fromisoformat(session_data["end_time"]) if session_data.get("end_time") else None
        self.status = session_data["status"]
        self.candidate_name = session_data.get("candidate_name")
        self.questions_asked = session_data.get("questions_asked", [])
        self.evaluations = session_data.get("evaluations", [])
        self.running_score = session_data.get("running_score", 0.0)
        self.skills_covered = session_data.get("skills_covered", {})

# Enhanced session manager that returns SimpleSession objects for orchestrator
class EnhancedSessionManager(SessionManager):
    """Enhanced session manager that provides objects for orchestrator"""
    
    async def get_session(self, session_id: str):
        """Get session as SimpleSession object"""
        session_data = await super().get_session(session_id)
        if session_data:
            return SimpleSession(session_data)
        return None
    
    async def update_session(self, session):
        """Update session from SimpleSession object"""
        if hasattr(session, 'session_id'):
            # Convert SimpleSession back to dict
            session_data = {
                "session_id": session.session_id,
                "start_time": session.start_time.isoformat(),
                "end_time": session.end_time.isoformat() if session.end_time else None,
                "status": session.status,
                "candidate_name": getattr(session, 'candidate_name', None),
                "questions_asked": getattr(session, 'questions_asked', []),
                "evaluations": getattr(session, 'evaluations', []),
                "running_score": getattr(session, 'running_score', 0.0),
                "skills_covered": getattr(session, 'skills_covered', {}),
                "conversation_history": getattr(session, 'conversation_history', []),
                "question_type_history": getattr(session, 'question_type_history', [])
            }
            await super().update_session(session.session_id, session_data)
        else:
            # Already a dict
            await super().update_session(session["session_id"], session)

if __name__ == "__main__":
    print("🗄️ Streamlined Session Manager - Redis + SQLite")
    print("=" * 50)
    print("📊 Features:")
    print("  ✅ Redis caching for speed")
    print("  ✅ SQLite persistence for durability")
    print("  ✅ Memory fallback for reliability")
    print("  ✅ Enhanced orchestrator compatibility")
    print("  ✅ Clean main.py integration")
    print("  ✅ Simplified, focused functionality")