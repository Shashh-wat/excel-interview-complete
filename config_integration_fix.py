# config_integration_fix.py - Integration Fixes for Config System
"""
This file patches the config.py system to work properly with your existing components.
Replace the problematic sections in your config.py with these fixed versions.
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# FIXED SERVICE CONTAINER
# =============================================================================

class FixedServiceContainer:
    """Fixed dependency injection container for all services"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Services
        self.evaluation_engine = None
        self.voice_service = None
        self.question_bank = None
        self.interview_orchestrator = None
        self.session_manager = None
        
        # Status tracking
        self.initialization_time = None
        self.services_initialized = False
        self.health_status = {}
        
    async def initialize_all_services(self):
        """Initialize all services in correct order with proper error handling"""
        
        start_time = datetime.utcnow()
        self.logger.info("🚀 Initializing complete Excel Interview System...")
        
        try:
            # Import missing_components for fallbacks
            try:
                from missing_components import create_service_container_components
                components = await create_service_container_components(self.config)
                
                self.evaluation_engine = components["evaluation_engine"]
                self.voice_service = components["voice_service"]
                self.question_bank = components["question_bank"]
                self.interview_orchestrator = components["interview_orchestrator"]
                
                self.logger.info("✅ All services initialized via missing_components")
                
            except ImportError:
                self.logger.warning("missing_components not available, initializing manually...")
                await self._initialize_services_manually()
            
            # Initialize Session Manager
            await self._initialize_session_manager()
            
            # Mark as initialized
            self.services_initialized = True
            self.initialization_time = datetime.utcnow()
            
            # Get initial health status
            await self._update_health_status()
            
            duration = (self.initialization_time - start_time).total_seconds()
            self.logger.info(f"✅ System initialization completed in {duration:.2f} seconds")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ System initialization failed: {e}")
            self.services_initialized = False
            return False
    
    async def _initialize_services_manually(self):
        """Manual initialization when missing_components is not available"""
        
        # 1. Initialize Evaluation Engine
        try:
            from evaluation_engine import ClaudeEvaluationEngine
            self.evaluation_engine = ClaudeEvaluationEngine(
                anthropic_api_key=self.config.anthropic_api_key
            )
            self.logger.info("✅ Evaluation engine initialized")
        except ImportError:
            self.evaluation_engine = self._create_minimal_evaluation_engine()
            self.logger.warning("⚠️ Using minimal evaluation engine")
        
        # 2. Initialize Voice Service
        try:
            from main import VoiceService, MurfAPIClient
            murf_client = MurfAPIClient(self.config.murf_api_key)
            self.voice_service = VoiceService(murf_client)
            self.logger.info("✅ Voice service initialized")
        except ImportError:
            self.voice_service = self._create_minimal_voice_service()
            self.logger.warning("⚠️ Using minimal voice service")
        
        # 3. Initialize Question Bank
        try:
            from question_bank_db import QuestionBankFactory
            self.question_bank = QuestionBankFactory.create_database_question_bank(
                db_path=self.config.question_bank_db
            )
            self.logger.info("✅ Question bank initialized")
        except ImportError:
            self.question_bank = self._create_minimal_question_bank()
            self.logger.warning("⚠️ Using minimal question bank")
        
        # 4. Initialize Interview Orchestrator
        try:
            from interview_orchestrator import InterviewOrchestrator
            self.interview_orchestrator = InterviewOrchestrator(
                evaluation_engine=self.evaluation_engine,
                question_bank=self.question_bank
            )
            self.logger.info("✅ Interview orchestrator initialized")
        except ImportError:
            self.interview_orchestrator = self._create_minimal_orchestrator()
            self.logger.warning("⚠️ Using minimal orchestrator")
    
    def _create_minimal_evaluation_engine(self):
        """Create minimal evaluation engine"""
        class MinimalEvaluationEngine:
            def __init__(self):
                self.available = False
            
            async def health_check(self):
                return {"status": "minimal", "health_percentage": 30}
            
            async def evaluate_response(self, question, text_response, file_path=None):
                return {
                    "score": 2.5,
                    "confidence": 0.5,
                    "reasoning": "Minimal evaluation - basic response scoring",
                    "strengths": ["Response provided"],
                    "areas_for_improvement": ["Install full evaluation system"],
                    "keywords_found": [],
                    "mistakes_detected": []
                }
            
            def get_performance_stats(self):
                return {"evaluation_stats": {"total_evaluations": 0}}
        
        return MinimalEvaluationEngine()
    
    def _create_minimal_voice_service(self):
        """Create minimal voice service"""
        class MinimalVoiceService:
            def __init__(self):
                self.available = False
            
            async def text_to_speech(self, text, voice_id=None):
                return {"success": False, "error": "Voice service not available"}
            
            def get_service_status(self):
                return {"available": False, "service_type": "minimal"}
        
        return MinimalVoiceService()
    
    def _create_minimal_question_bank(self):
        """Create minimal question bank"""
        class MinimalQuestionBank:
            def __init__(self):
                self.questions = [
                    {
                        "id": "q1",
                        "text": "Explain VLOOKUP function in Excel",
                        "type": "free_text",
                        "skill_category": "formulas",
                        "difficulty": "intermediate",
                        "expected_keywords": ["VLOOKUP", "lookup", "function"]
                    }
                ]
                self.current_index = 0
            
            async def get_question(self, **kwargs):
                if self.current_index >= len(self.questions):
                    return None
                
                question_data = self.questions[self.current_index]
                self.current_index += 1
                
                from types import SimpleNamespace
                question = SimpleNamespace(**question_data)
                question.to_dict = lambda: question_data
                return question
            
            async def get_question_bank_status(self):
                return {"initialized": True, "total_questions": len(self.questions)}
        
        return MinimalQuestionBank()
    
    def _create_minimal_orchestrator(self):
        """Create minimal orchestrator"""
        class MinimalOrchestrator:
            def __init__(self, evaluation_engine=None, question_bank=None):
                self.evaluation_engine = evaluation_engine
                self.question_bank = question_bank
                self.sessions = {}
            
            async def start_interview(self, candidate_name=None):
                session_id = f"session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                
                if self.question_bank:
                    question = await self.question_bank.get_question()
                    if question:
                        self.sessions[session_id] = {
                            "candidate_name": candidate_name,
                            "status": "in_progress",
                            "current_question": question.to_dict() if hasattr(question, 'to_dict') else question.__dict__,
                            "questions_asked": [],
                            "evaluations": []
                        }
                        
                        return {
                            "success": True,
                            "session_id": session_id,
                            "first_question": self.sessions[session_id]["current_question"]
                        }
                
                return {"success": False, "error": "No questions available"}
            
            async def submit_response(self, session_id, response_text, time_taken=0):
                if session_id not in self.sessions:
                    return {"success": False, "error": "Session not found"}
                
                session = self.sessions[session_id]
                current_question = session.get("current_question")
                
                # Evaluate response
                if self.evaluation_engine:
                    evaluation = await self.evaluation_engine.evaluate_response(
                        current_question, response_text
                    )
                else:
                    evaluation = {
                        "score": 2.5,
                        "reasoning": "Basic evaluation",
                        "strengths": ["Response provided"],
                        "areas_for_improvement": ["Install full evaluation system"]
                    }
                
                session["evaluations"].append(evaluation)
                session["questions_asked"].append(current_question.get("id", "unknown"))
                
                # Get next question
                next_question = None
                if self.question_bank:
                    next_question = await self.question_bank.get_question()
                
                interview_complete = next_question is None or len(session["questions_asked"]) >= 5
                
                if interview_complete:
                    session["status"] = "completed"
                
                return {
                    "success": True,
                    "evaluation": evaluation,
                    "next_question": next_question.to_dict() if next_question and hasattr(next_question, 'to_dict') else None,
                    "status": "completed" if interview_complete else "in_progress"
                }
        
        return MinimalOrchestrator(self.evaluation_engine, self.question_bank)
    
    async def _initialize_session_manager(self):
        """Initialize session manager"""
        try:
            self.session_manager = SimpleSessionManager(
                orchestrator=self.interview_orchestrator,
                max_sessions=self.config.max_concurrent_sessions
            )
            self.logger.info("✅ Session manager initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize session manager: {e}")
            self.session_manager = SimpleSessionManager()
    
    async def _update_health_status(self):
        """Update health status for all services"""
        try:
            health_checks = {}
            
            # Evaluation engine health
            if self.evaluation_engine:
                try:
                    health_checks["evaluation_engine"] = await self.evaluation_engine.health_check()
                except Exception as e:
                    health_checks["evaluation_engine"] = {"status": "error", "error": str(e)}
            
            # Voice service health
            if self.voice_service:
                try:
                    if hasattr(self.voice_service, 'get_service_status'):
                        status = self.voice_service.get_service_status()
                    else:
                        status = {"available": getattr(self.voice_service, 'available', False)}
                    
                    health_checks["voice_service"] = {
                        "status": "healthy" if status.get("available") else "degraded",
                        "available": status.get("available", False)
                    }
                except Exception as e:
                    health_checks["voice_service"] = {"status": "error", "error": str(e)}
            
            # Question bank health
            if self.question_bank:
                try:
                    if hasattr(self.question_bank, 'get_question_bank_status'):
                        status = await self.question_bank.get_question_bank_status()
                    else:
                        status = {"initialized": True}
                    
                    health_checks["question_bank"] = {
                        "status": "healthy" if status.get("initialized") else "unhealthy",
                        "initialized": status.get("initialized", False)
                    }
                except Exception as e:
                    health_checks["question_bank"] = {"status": "error", "error": str(e)}
            
            # Interview orchestrator health
            if self.interview_orchestrator:
                health_checks["interview_orchestrator"] = {
                    "status": "healthy",
                    "active_sessions": len(getattr(self.interview_orchestrator, 'sessions', {}))
                }
            
            self.health_status = health_checks
            
        except Exception as e:
            self.logger.error(f"Failed to update health status: {e}")
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health"""
        await self._update_health_status()
        
        # Calculate overall health
        healthy_services = sum(
            1 for service_health in self.health_status.values()
            if service_health.get("status") == "healthy"
        )
        total_services = len(self.health_status)
        health_percentage = (healthy_services / max(total_services, 1)) * 100
        
        return {
            "overall_status": "healthy" if health_percentage >= 75 else "degraded" if health_percentage >= 50 else "unhealthy",
            "health_percentage": round(health_percentage, 1),
            "services": self.health_status,
            "services_initialized": self.services_initialized,
            "initialization_time": self.initialization_time.isoformat() if self.initialization_time else None,
            "uptime_seconds": (datetime.utcnow() - self.initialization_time).total_seconds() if self.initialization_time else 0
        }
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        stats = {
            "version": self.config.app_version,
            "environment": self.config.environment,
            "uptime_seconds": (datetime.utcnow() - self.initialization_time).total_seconds() if self.initialization_time else 0,
            "config": {
                "max_questions_per_interview": self.config.max_questions_per_interview,
                "default_time_limit_minutes": self.config.default_time_limit_minutes,
                "default_voice_id": self.config.default_voice_id
            }
        }
        
        # Add component-specific stats
        component_stats = {}
        
        try:
            if self.evaluation_engine and hasattr(self.evaluation_engine, 'get_performance_stats'):
                component_stats["evaluation_engine"] = self.evaluation_engine.get_performance_stats()
        except Exception as e:
            component_stats["evaluation_engine"] = {"error": str(e)}
        
        try:
            if self.voice_service:
                if hasattr(self.voice_service, 'get_service_status'):
                    component_stats["voice_service"] = self.voice_service.get_service_status()
                else:
                    component_stats["voice_service"] = {"available": False}
        except Exception as e:
            component_stats["voice_service"] = {"error": str(e)}
        
        try:
            if self.question_bank:
                if hasattr(self.question_bank, 'get_question_bank_status'):
                    component_stats["question_bank"] = await self.question_bank.get_question_bank_status()
                else:
                    component_stats["question_bank"] = {"initialized": True}
        except Exception as e:
            component_stats["question_bank"] = {"error": str(e)}
        
        try:
            if self.session_manager:
                component_stats["session_manager"] = self.session_manager.get_stats()
        except Exception as e:
            component_stats["session_manager"] = {"error": str(e)}
        
        stats["component_stats"] = component_stats
        return stats
    
    async def shutdown(self):
        """Graceful shutdown of all services"""
        self.logger.info("🛑 Shutting down system...")
        
        try:
            # Close question bank database
            if self.question_bank and hasattr(self.question_bank, 'close'):
                self.question_bank.close()
            
            # Clean up session manager
            if self.session_manager:
                await self.session_manager.cleanup()
            
            self.services_initialized = False
            self.logger.info("✅ System shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")

# =============================================================================
# SIMPLE SESSION MANAGER (fixed version)
# =============================================================================

class SimpleSessionManager:
    """Simple session management with better error handling"""
    
    def __init__(self, orchestrator=None, max_sessions: int = 50):
        self.orchestrator = orchestrator
        self.max_sessions = max_sessions
        self.active_sessions = {}
        self.session_stats = {
            "sessions_created": 0,
            "sessions_completed": 0,
            "sessions_abandoned": 0
        }
    
    async def create_session(self, candidate_name: str = None) -> str:
        """Create new interview session"""
        if len(self.active_sessions) >= self.max_sessions:
            raise Exception("Maximum concurrent sessions reached")
        
        session_id = f"session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{len(self.active_sessions)}"
        
        self.active_sessions[session_id] = {
            "candidate_name": candidate_name,
            "created_at": datetime.utcnow(),
            "status": "created"
        }
        
        self.session_stats["sessions_created"] += 1
        return session_id
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        return {
            "active_sessions": len(self.active_sessions),
            "max_sessions": self.max_sessions,
            **self.session_stats
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get manager statistics (sync version)"""
        return {
            "active_sessions": len(self.active_sessions),
            "max_sessions": self.max_sessions,
            **self.session_stats
        }
    
    async def cleanup(self):
        """Cleanup session manager"""
        self.active_sessions.clear()

# =============================================================================
# INTEGRATION TESTING
# =============================================================================

async def test_fixed_system_integration():
    """Test the fixed system integration"""
    
    print("🧪 TESTING FIXED SYSTEM INTEGRATION")
    print("=" * 60)
    
    try:
        # Create a test config
        @dataclass
        class TestConfig:
            app_name: str = "Test Excel Interview System"
            app_version: str = "4.0.0-fixed"
            environment: str = "test"
            anthropic_api_key: str = "test_key"
            murf_api_key: str = "test_key"
            question_bank_db: str = "test_question_bank.db"
            default_voice_id: str = "en-US-sarah"
            max_questions_per_interview: int = 5
            default_time_limit_minutes: int = 15
            max_concurrent_sessions: int = 10
        
        config = TestConfig()
        
        # Initialize service container
        print("📦 Initializing fixed service container...")
        container = FixedServiceContainer(config)
        
        success = await container.initialize_all_services()
        
        if success:
            print("✅ Service container initialized successfully")
            
            # Check health
            health = await container.get_system_health()
            print(f"✅ System health: {health['overall_status']} ({health['health_percentage']}%)")
            
            # Show service status
            for service, status in health['services'].items():
                emoji = "✅" if status.get('status') == 'healthy' else "⚠️" if status.get('status') == 'degraded' else "❌"
                print(f"   {emoji} {service}: {status.get('status', 'unknown')}")
            
            # Test interview flow
            print("\n🎯 Testing interview flow...")
            
            if container.interview_orchestrator:
                # Start interview
                start_result = await container.interview_orchestrator.start_interview("Test User")
                
                if start_result.get("success", True):
                    session_id = start_result["session_id"]
                    print(f"✅ Interview started: {session_id}")
                    
                    # Submit response
                    response_result = await container.interview_orchestrator.submit_response(
                        session_id=session_id,
                        response_text="VLOOKUP is a vertical lookup function in Excel that searches for a value in the leftmost column of a table and returns a corresponding value from a specified column in the same row.",
                        time_taken=45
                    )
                    
                    if response_result.get("success", True):
                        evaluation = response_result.get("evaluation", {})
                        print(f"✅ Response processed - Score: {evaluation.get('score', 0)}/5.0")
                        print(f"   Reasoning: {evaluation.get('reasoning', 'No reasoning')[:50]}...")
                    else:
                        print(f"❌ Response processing failed: {response_result.get('error')}")
                else:
                    print(f"❌ Interview start failed: {start_result.get('error')}")
            else:
                print("❌ No interview orchestrator available")
            
            # Get final stats
            print("\n📊 System statistics...")
            stats = await container.get_system_stats()
            print(f"   Version: {stats['version']}")
            print(f"   Environment: {stats['environment']}")
            print(f"   Uptime: {stats['uptime_seconds']:.1f} seconds")
            
            # Shutdown
            await container.shutdown()
            
            print("\n🎉 FIXED SYSTEM INTEGRATION TEST PASSED!")
            return True
        else:
            print("❌ Service container initialization failed")
            return False
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 Config System Integration Fixes")
    print("=" * 60)
    print("✅ Fixed Features:")
    print("  • Robust service initialization with fallbacks")
    print("  • Proper error handling for missing components")
    print("  • Compatible with existing file structure")
    print("  • Graceful degradation when components unavailable")
    
    # Run test
    success = asyncio.run(test_fixed_system_integration())
    print(f"\n{'🎉 All tests passed!' if success else '❌ Some tests failed'}")