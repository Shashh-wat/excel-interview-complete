# question_bank_db.py - Enhanced Question Bank with Database Support
"""
Comprehensive question bank management system with SQLite database storage,
intelligent question selection, performance tracking, and voice optimization.
"""

import sqlite3
import asyncio
import logging
import uuid
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from contextlib import asynccontextmanager

# Import models
try:
    from models import (
        Question, SkillCategory, DifficultyLevel, QuestionType,
        create_question, dict_to_question
    )
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False
    logging.warning("models.py not available - using fallback")

# Configure logging
logger = logging.getLogger(__name__)

# =============================================================================
# FALLBACK MODELS (if models.py not available)
# =============================================================================

if not MODELS_AVAILABLE:
    from enum import Enum
    from dataclasses import dataclass
    from typing import List
    
    class SkillCategory(Enum):
        FORMULAS = "formulas"
        DATA_MANIPULATION = "data_manipulation"
        PIVOT_TABLES = "pivot_tables"
        DATA_ANALYSIS = "data_analysis"
        DATA_VISUALIZATION = "data_visualization"
        ERROR_HANDLING = "error_handling"
    
    class DifficultyLevel(Enum):
        BEGINNER = "beginner"
        INTERMEDIATE = "intermediate"
        ADVANCED = "advanced"
    
    class QuestionType(Enum):
        FREE_TEXT = "free_text"
        FILE_UPLOAD = "file_upload"
        HYBRID = "hybrid"
    
    @dataclass
    class Question:
        id: str
        text: str
        type: str
        skill_category: str
        difficulty: str
        expected_keywords: List[str] = None
        
        def to_dict(self):
            return {
                "id": self.id,
                "text": self.text,
                "type": self.type,
                "skill_category": self.skill_category,
                "difficulty": self.difficulty,
                "expected_keywords": self.expected_keywords or []
            }

# =============================================================================
# DATABASE SCHEMA
# =============================================================================

CREATE_QUESTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS questions (
    id TEXT PRIMARY KEY,
    text TEXT NOT NULL,
    type TEXT NOT NULL,
    skill_category TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    estimated_time_minutes INTEGER DEFAULT 5,
    expected_keywords TEXT,  -- JSON array
    common_mistakes TEXT,    -- JSON array
    scoring_criteria TEXT,   -- JSON object
    voice_optimized BOOLEAN DEFAULT 0,
    usage_count INTEGER DEFAULT 0,
    avg_score REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_QUESTION_RESPONSES_TABLE = """
CREATE TABLE IF NOT EXISTS question_responses (
    id TEXT PRIMARY KEY,
    question_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    response_text TEXT,
    file_path TEXT,
    evaluation_score REAL,
    evaluation_data TEXT,  -- JSON object
    transcription_confidence REAL,
    time_taken_seconds INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (question_id) REFERENCES questions (id)
);
"""

CREATE_QUESTION_ANALYTICS_TABLE = """
CREATE TABLE IF NOT EXISTS question_analytics (
    id TEXT PRIMARY KEY,
    question_id TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    session_id TEXT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (question_id) REFERENCES questions (id)
);
"""

# =============================================================================
# ENHANCED QUESTION BANK MANAGER
# =============================================================================

class EnhancedQuestionBankManager:
    """Enhanced question bank with database storage and intelligent selection"""
    
    def __init__(self, db_path: str = "question_bank.db", claude_client=None):
        self.db_path = db_path
        self.claude_client = claude_client
        self.logger = logging.getLogger(__name__)
        
        # Initialize database
        self.db_connection = None
        self.initialized = False
        
        # Question selection strategies
        self.selection_strategies = {
            "sequential": self._sequential_selection,
            "adaptive": self._adaptive_selection,
            "adaptive_voice": self._adaptive_voice_selection,
            "skill_based": self._skill_based_selection,
            "difficulty_adaptive": self._difficulty_adaptive_selection
        }
        
        # Performance tracking
        self.stats = {
            "questions_served": 0,
            "unique_sessions": set(),
            "avg_response_time": 0.0,
            "cache_hits": 0,
            "strategy_usage": {}
        }
        
        # Question cache
        self.question_cache = {}
        self.last_cache_update = None
        
    async def initialize(self, populate_sample_data: bool = True):
        """Initialize the question bank database"""
        
        try:
            # Create database directory if needed
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Initialize database
            self.db_connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.db_connection.row_factory = sqlite3.Row
            
            # Create tables
            self.db_connection.execute(CREATE_QUESTIONS_TABLE)
            self.db_connection.execute(CREATE_QUESTION_RESPONSES_TABLE)
            self.db_connection.execute(CREATE_QUESTION_ANALYTICS_TABLE)
            self.db_connection.commit()
            
            # Populate sample data if requested
            if populate_sample_data:
                await self._populate_sample_questions()
            
            # Update cache
            await self._update_question_cache()
            
            self.initialized = True
            self.logger.info(f"✅ Question bank initialized: {self.db_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize question bank: {e}")
            self.initialized = False
            return False
    
    async def _populate_sample_questions(self):
        """Populate database with comprehensive Excel questions"""
        
        sample_questions = [
            # FORMULAS - Beginner
            {
                "id": "excel_formulas_01",
                "text": "Explain what the SUM function does in Excel and provide a simple example of how to use it.",
                "type": "free_text",
                "skill_category": "formulas",
                "difficulty": "beginner",
                "estimated_time_minutes": 3,
                "expected_keywords": ["SUM", "function", "add", "range", "formula", "=SUM"],
                "voice_optimized": True
            },
            {
                "id": "excel_formulas_02", 
                "text": "What is the difference between absolute and relative cell references in Excel? Give examples.",
                "type": "free_text",
                "skill_category": "formulas",
                "difficulty": "beginner",
                "estimated_time_minutes": 4,
                "expected_keywords": ["absolute", "relative", "reference", "$", "A1", "$A$1", "copy", "formula"],
                "voice_optimized": True
            },
            
            # FORMULAS - Intermediate  
            {
                "id": "excel_formulas_03",
                "text": "Explain the difference between VLOOKUP and INDEX-MATCH functions. When would you use each one?",
                "type": "free_text",
                "skill_category": "formulas",
                "difficulty": "intermediate",
                "estimated_time_minutes": 6,
                "expected_keywords": ["VLOOKUP", "INDEX", "MATCH", "lookup", "table", "flexible", "left", "right"],
                "voice_optimized": True
            },
            {
                "id": "excel_formulas_04",
                "text": "How do you use SUMIF and COUNTIF functions? Provide examples with criteria.",
                "type": "free_text",
                "skill_category": "formulas",
                "difficulty": "intermediate",
                "estimated_time_minutes": 5,
                "expected_keywords": ["SUMIF", "COUNTIF", "criteria", "range", "condition", "greater than", "less than"],
                "voice_optimized": True
            },
            
            # FORMULAS - Advanced
            {
                "id": "excel_formulas_05",
                "text": "Explain array formulas in Excel. How do you create and use them effectively?",
                "type": "free_text",
                "skill_category": "formulas",
                "difficulty": "advanced",
                "estimated_time_minutes": 8,
                "expected_keywords": ["array", "formula", "Ctrl+Shift+Enter", "curly braces", "multiple", "calculations"],
                "voice_optimized": False
            },
            
            # DATA MANIPULATION - Beginner
            {
                "id": "excel_data_01",
                "text": "How do you sort data in Excel? Explain both single-column and multi-column sorting.",
                "type": "free_text",
                "skill_category": "data_manipulation",
                "difficulty": "beginner",
                "estimated_time_minutes": 4,
                "expected_keywords": ["sort", "ascending", "descending", "Data tab", "multiple columns", "criteria"],
                "voice_optimized": True
            },
            {
                "id": "excel_data_02",
                "text": "What is conditional formatting and how do you apply it to highlight important data?",
                "type": "free_text",
                "skill_category": "data_manipulation",
                "difficulty": "beginner",
                "estimated_time_minutes": 5,
                "expected_keywords": ["conditional formatting", "highlight", "rules", "color", "format", "criteria"],
                "voice_optimized": True
            },
            
            # DATA MANIPULATION - Intermediate
            {
                "id": "excel_data_03",
                "text": "Describe how to use Excel's Filter and Advanced Filter features for data analysis.",
                "type": "free_text",
                "skill_category": "data_manipulation",
                "difficulty": "intermediate",
                "estimated_time_minutes": 6,
                "expected_keywords": ["filter", "advanced filter", "criteria", "unique", "copy", "in-place"],
                "voice_optimized": True
            },
            {
                "id": "excel_data_04",
                "text": "How do you remove duplicates from a dataset in Excel? What are the different methods?",
                "type": "free_text",
                "skill_category": "data_manipulation",
                "difficulty": "intermediate",
                "estimated_time_minutes": 5,
                "expected_keywords": ["remove duplicates", "Data tab", "unique", "advanced filter", "COUNTIF"],
                "voice_optimized": True
            },
            
            # PIVOT TABLES - Intermediate
            {
                "id": "excel_pivot_01",
                "text": "Explain how to create a pivot table in Excel. What are the key components and benefits?",
                "type": "free_text",
                "skill_category": "pivot_tables",
                "difficulty": "intermediate",
                "estimated_time_minutes": 7,
                "expected_keywords": ["pivot table", "Insert", "rows", "columns", "values", "summarize", "drag", "field"],
                "voice_optimized": True
            },
            {
                "id": "excel_pivot_02",
                "text": "How do you add calculated fields to a pivot table? Provide an example scenario.",
                "type": "free_text",
                "skill_category": "pivot_tables",
                "difficulty": "intermediate",
                "estimated_time_minutes": 6,
                "expected_keywords": ["calculated field", "formula", "PivotTable Tools", "Fields", "Items", "Sets"],
                "voice_optimized": True
            },
            
            # ERROR HANDLING - Intermediate
            {
                "id": "excel_errors_01",
                "text": "What are the most common Excel errors (#N/A, #REF!, #VALUE!, etc.) and how do you fix them?",
                "type": "free_text",
                "skill_category": "error_handling",
                "difficulty": "intermediate",
                "estimated_time_minutes": 6,
                "expected_keywords": ["#N/A", "#REF!", "#VALUE!", "#DIV/0!", "#NAME?", "IFERROR", "troubleshoot"],
                "voice_optimized": True
            },
            {
                "id": "excel_errors_02",
                "text": "How do you use IFERROR and ISERROR functions to handle errors gracefully in formulas?",
                "type": "free_text",
                "skill_category": "error_handling",
                "difficulty": "intermediate",
                "estimated_time_minutes": 5,
                "expected_keywords": ["IFERROR", "ISERROR", "error handling", "graceful", "alternative", "message"],
                "voice_optimized": True
            },
            
            # DATA VISUALIZATION - Intermediate
            {
                "id": "excel_viz_01",
                "text": "How do you create different types of charts in Excel? When would you use each type?",
                "type": "free_text",
                "skill_category": "data_visualization",
                "difficulty": "intermediate",
                "estimated_time_minutes": 7,
                "expected_keywords": ["chart", "graph", "column", "line", "pie", "scatter", "Insert", "visualization"],
                "voice_optimized": True
            },
            
            # HYBRID QUESTIONS (Text + File)
            {
                "id": "excel_hybrid_01",
                "text": "Create a spreadsheet that demonstrates VLOOKUP usage with sample data. Explain your approach.",
                "type": "hybrid",
                "skill_category": "formulas",
                "difficulty": "intermediate",
                "estimated_time_minutes": 10,
                "expected_keywords": ["VLOOKUP", "spreadsheet", "sample data", "lookup table", "exact match"],
                "voice_optimized": False
            },
            {
                "id": "excel_hybrid_02",
                "text": "Build a pivot table from provided data and explain the insights it reveals.",
                "type": "hybrid",
                "skill_category": "pivot_tables",
                "difficulty": "intermediate",
                "estimated_time_minutes": 12,
                "expected_keywords": ["pivot table", "data analysis", "insights", "summarize", "trends"],
                "voice_optimized": False
            }
        ]
        
        # Insert questions into database
        for question_data in sample_questions:
            await self._insert_question(question_data)
        
        self.logger.info(f"✅ Populated {len(sample_questions)} sample questions")
    
    async def _insert_question(self, question_data: Dict[str, Any]):
        """Insert a question into the database"""
        
        try:
            cursor = self.db_connection.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO questions 
                (id, text, type, skill_category, difficulty, estimated_time_minutes, 
                 expected_keywords, voice_optimized, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                question_data["id"],
                question_data["text"],
                question_data["type"],
                question_data["skill_category"],
                question_data["difficulty"],
                question_data.get("estimated_time_minutes", 5),
                json.dumps(question_data.get("expected_keywords", [])),
                question_data.get("voice_optimized", True),
                datetime.utcnow().isoformat(),
                datetime.utcnow().isoformat()
            ))
            
            self.db_connection.commit()
            
        except Exception as e:
            self.logger.error(f"Failed to insert question {question_data.get('id')}: {e}")
            raise
    
    async def get_question(
        self,
        strategy: str = "adaptive_voice",
        session_state: Dict[str, Any] = None,
        skill_category: str = None,
        difficulty: str = None,
        question_type: str = None
    ) -> Optional[Question]:
        """Get next question using specified strategy"""
        
        try:
            if not self.initialized:
                await self.initialize()
            
            # Update stats
            self.stats["questions_served"] += 1
            self.stats["strategy_usage"][strategy] = self.stats["strategy_usage"].get(strategy, 0) + 1
            
            if session_state:
                self.stats["unique_sessions"].add(session_state.get("session_id", "unknown"))
            
            # Use selection strategy
            if strategy in self.selection_strategies:
                question_data = await self.selection_strategies[strategy](
                    session_state, skill_category, difficulty, question_type
                )
            else:
                # Default to adaptive voice selection
                question_data = await self._adaptive_voice_selection(
                    session_state, skill_category, difficulty, question_type
                )
            
            if question_data:
                # Update usage count
                await self._update_question_usage(question_data["id"])
                
                # Convert to Question object
                return self._create_question_object(question_data)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get question: {e}")
            return None
    
    async def _sequential_selection(
        self,
        session_state: Dict[str, Any] = None,
        skill_category: str = None,
        difficulty: str = None,
        question_type: str = None
    ) -> Optional[Dict[str, Any]]:
        """Sequential question selection"""
        
        try:
            cursor = self.db_connection.cursor()
            
            # Get questions not yet asked in this session
            asked_questions = session_state.get("questions_asked", []) if session_state else []
            
            placeholders = ",".join("?" for _ in asked_questions) if asked_questions else "NULL"
            query = f"""
                SELECT * FROM questions 
                WHERE id NOT IN ({placeholders if asked_questions else 'SELECT NULL WHERE 1=0'})
                ORDER BY created_at ASC
                LIMIT 1
            """
            
            cursor.execute(query, asked_questions)
            row = cursor.fetchone()
            
            return dict(row) if row else None
            
        except Exception as e:
            self.logger.error(f"Sequential selection failed: {e}")
            return None
    
    async def _adaptive_selection(
        self,
        session_state: Dict[str, Any] = None,
        skill_category: str = None,
        difficulty: str = None,
        question_type: str = None
    ) -> Optional[Dict[str, Any]]:
        """Adaptive question selection based on performance"""
        
        try:
            if not session_state:
                return await self._sequential_selection()
            
            cursor = self.db_connection.cursor()
            asked_questions = session_state.get("questions_asked", [])
            evaluations = session_state.get("evaluations", [])
            
            # Calculate current performance
            if evaluations:
                avg_score = sum(e.get("score", 0) for e in evaluations) / len(evaluations)
                
                # Adjust difficulty based on performance
                if avg_score >= 4.0:
                    target_difficulty = "advanced"
                elif avg_score >= 2.5:
                    target_difficulty = "intermediate"
                else:
                    target_difficulty = "beginner"
            else:
                target_difficulty = "intermediate"  # Start with intermediate
            
            # Get skills covered
            skills_covered = session_state.get("skills_covered", {})
            
            # Prioritize uncovered skills
            placeholders = ",".join("?" for _ in asked_questions) if asked_questions else "NULL"
            query = f"""
                SELECT *, 
                       CASE WHEN skill_category NOT IN ({','.join('?' for _ in skills_covered.keys()) if skills_covered else 'SELECT NULL WHERE 1=0'}) 
                            THEN 1 ELSE 0 END as priority_score
                FROM questions 
                WHERE id NOT IN ({placeholders if asked_questions else 'SELECT NULL WHERE 1=0'})
                  AND difficulty = ?
                ORDER BY priority_score DESC, usage_count ASC, RANDOM()
                LIMIT 1
            """
            
            params = asked_questions + list(skills_covered.keys()) + [target_difficulty]
            cursor.execute(query, params)
            row = cursor.fetchone()
            
            # If no question found with target difficulty, try any difficulty
            if not row:
                query = f"""
                    SELECT * FROM questions 
                    WHERE id NOT IN ({placeholders if asked_questions else 'SELECT NULL WHERE 1=0'})
                    ORDER BY usage_count ASC, RANDOM()
                    LIMIT 1
                """
                cursor.execute(query, asked_questions)
                row = cursor.fetchone()
            
            return dict(row) if row else None
            
        except Exception as e:
            self.logger.error(f"Adaptive selection failed: {e}")
            return await self._sequential_selection(session_state)
    
    async def _adaptive_voice_selection(
        self,
        session_state: Dict[str, Any] = None,
        skill_category: str = None,
        difficulty: str = None,
        question_type: str = None
    ) -> Optional[Dict[str, Any]]:
        """Voice-optimized adaptive selection"""
        
        try:
            # First try adaptive selection with voice optimization
            cursor = self.db_connection.cursor()
            asked_questions = session_state.get("questions_asked", []) if session_state else []
            
            # Prefer voice-optimized questions
            placeholders = ",".join("?" for _ in asked_questions) if asked_questions else "NULL"
            query = f"""
                SELECT * FROM questions 
                WHERE id NOT IN ({placeholders if asked_questions else 'SELECT NULL WHERE 1=0'})
                  AND voice_optimized = 1
                  AND type = 'free_text'  -- Voice works better with text responses
                ORDER BY usage_count ASC, RANDOM()
                LIMIT 1
            """
            
            cursor.execute(query, asked_questions)
            row = cursor.fetchone()
            
            # If no voice-optimized question found, fall back to adaptive selection
            if not row:
                return await self._adaptive_selection(session_state, skill_category, difficulty, question_type)
            
            return dict(row)
            
        except Exception as e:
            self.logger.error(f"Adaptive voice selection failed: {e}")
            return await self._adaptive_selection(session_state, skill_category, difficulty, question_type)
    
    async def _skill_based_selection(
        self,
        session_state: Dict[str, Any] = None,
        skill_category: str = None,
        difficulty: str = None,
        question_type: str = None
    ) -> Optional[Dict[str, Any]]:
        """Skill-based question selection"""
        
        try:
            cursor = self.db_connection.cursor()
            asked_questions = session_state.get("questions_asked", []) if session_state else []
            
            placeholders = ",".join("?" for _ in asked_questions) if asked_questions else "NULL"
            
            params = asked_questions
            where_clauses = [f"id NOT IN ({placeholders if asked_questions else 'SELECT NULL WHERE 1=0'})"]
            
            if skill_category:
                where_clauses.append("skill_category = ?")
                params.append(skill_category)
            
            if difficulty:
                where_clauses.append("difficulty = ?")
                params.append(difficulty)
            
            if question_type:
                where_clauses.append("type = ?")
                params.append(question_type)
            
            query = f"""
                SELECT * FROM questions 
                WHERE {' AND '.join(where_clauses)}
                ORDER BY usage_count ASC, RANDOM()
                LIMIT 1
            """
            
            cursor.execute(query, params)
            row = cursor.fetchone()
            
            return dict(row) if row else None
            
        except Exception as e:
            self.logger.error(f"Skill-based selection failed: {e}")
            return None
    
    async def _difficulty_adaptive_selection(
        self,
        session_state: Dict[str, Any] = None,
        skill_category: str = None,
        difficulty: str = None,
        question_type: str = None
    ) -> Optional[Dict[str, Any]]:
        """Difficulty-adaptive selection"""
        
        # This is similar to adaptive selection but focuses more on difficulty progression
        return await self._adaptive_selection(session_state, skill_category, difficulty, question_type)
    
    def _create_question_object(self, question_data: Dict[str, Any]) -> Question:
        """Create Question object from database row"""
        
        try:
            # Parse JSON fields
            expected_keywords = json.loads(question_data.get("expected_keywords", "[]"))
            
            if MODELS_AVAILABLE:
                return Question(
                    id=question_data["id"],
                    text=question_data["text"],
                    type=QuestionType(question_data["type"]),
                    skill_category=SkillCategory(question_data["skill_category"]),
                    difficulty=DifficultyLevel(question_data["difficulty"]),
                    estimated_time_minutes=question_data.get("estimated_time_minutes", 5),
                    expected_keywords=expected_keywords
                )
            else:
                # Fallback Question object
                return Question(
                    id=question_data["id"],
                    text=question_data["text"],
                    type=question_data["type"],
                    skill_category=question_data["skill_category"],
                    difficulty=question_data["difficulty"],
                    expected_keywords=expected_keywords
                )
                
        except Exception as e:
            self.logger.error(f"Failed to create question object: {e}")
            raise
    
    async def record_question_response(
        self,
        question_id: str,
        session_id: str,
        evaluation: Dict[str, Any],
        response_text: str = None,
        file_path: str = None,
        transcription_confidence: float = None,
        time_taken: int = None
    ):
        """Record a question response and evaluation"""
        
        try:
            cursor = self.db_connection.cursor()
            
            response_id = str(uuid.uuid4())
            
            cursor.execute("""
                INSERT INTO question_responses
                (id, question_id, session_id, response_text, file_path, 
                 evaluation_score, evaluation_data, transcription_confidence, 
                 time_taken_seconds, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                response_id,
                question_id,
                session_id,
                response_text,
                file_path,
                evaluation.get("score"),
                json.dumps(evaluation),
                transcription_confidence,
                time_taken,
                datetime.utcnow().isoformat()
            ))
            
            # Update question statistics
            await self._update_question_stats(question_id, evaluation.get("score", 0))
            
            self.db_connection.commit()
            
        except Exception as e:
            self.logger.error(f"Failed to record question response: {e}")
    
    async def _update_question_usage(self, question_id: str):
        """Update question usage count"""
        
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                UPDATE questions 
                SET usage_count = usage_count + 1,
                    updated_at = ?
                WHERE id = ?
            """, (datetime.utcnow().isoformat(), question_id))
            self.db_connection.commit()
            
        except Exception as e:
            self.logger.error(f"Failed to update question usage: {e}")
    
    async def _update_question_stats(self, question_id: str, score: float):
        """Update question performance statistics"""
        
        try:
            cursor = self.db_connection.cursor()
            
            # Get current stats
            cursor.execute("SELECT usage_count, avg_score FROM questions WHERE id = ?", (question_id,))
            row = cursor.fetchone()
            
            if row:
                current_count = row["usage_count"]
                current_avg = row["avg_score"]
                
                # Calculate new average
                new_avg = ((current_avg * (current_count - 1)) + score) / current_count
                
                cursor.execute("""
                    UPDATE questions 
                    SET avg_score = ?,
                        updated_at = ?
                    WHERE id = ?
                """, (new_avg, datetime.utcnow().isoformat(), question_id))
                
                self.db_connection.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to update question stats: {e}")
    
    async def _update_question_cache(self):
        """Update in-memory question cache"""
        
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT * FROM questions")
            rows = cursor.fetchall()
            
            self.question_cache = {row["id"]: dict(row) for row in rows}
            self.last_cache_update = datetime.utcnow()
            
        except Exception as e:
            self.logger.error(f"Failed to update question cache: {e}")
    
    async def get_question_bank_status(self) -> Dict[str, Any]:
        """Get comprehensive question bank status"""
        
        try:
            if not self.initialized:
                return {
                    "initialized": False,
                    "error": "Question bank not initialized"
                }
            
            cursor = self.db_connection.cursor()
            
            # Get question statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_questions,
                    COUNT(DISTINCT skill_category) as skill_categories,
                    COUNT(DISTINCT difficulty) as difficulty_levels,
                    SUM(usage_count) as total_usage,
                    AVG(avg_score) as overall_avg_score,
                    COUNT(CASE WHEN voice_optimized = 1 THEN 1 END) as voice_optimized_count
                FROM questions
            """)
            
            stats_row = cursor.fetchone()
            
            # Get skill category breakdown
            cursor.execute("""
                SELECT skill_category, COUNT(*) as count, AVG(avg_score) as avg_score
                FROM questions 
                GROUP BY skill_category
            """)
            skill_breakdown = {row["skill_category"]: {"count": row["count"], "avg_score": row["avg_score"]} 
                              for row in cursor.fetchall()}
            
            # Get difficulty breakdown
            cursor.execute("""
                SELECT difficulty, COUNT(*) as count, AVG(avg_score) as avg_score
                FROM questions 
                GROUP BY difficulty
            """)
            difficulty_breakdown = {row["difficulty"]: {"count": row["count"], "avg_score": row["avg_score"]} 
                                   for row in cursor.fetchall()}
            
            # Get recent activity
            cursor.execute("""
                SELECT COUNT(*) as recent_responses
                FROM question_responses 
                WHERE created_at >= datetime('now', '-24 hours')
            """)
            recent_activity = cursor.fetchone()["recent_responses"]
            
            return {
                "initialized": True,
                "database_path": self.db_path,
                "question_statistics": {
                    "total_questions": stats_row["total_questions"],
                    "skill_categories": stats_row["skill_categories"],
                    "difficulty_levels": stats_row["difficulty_levels"],
                    "voice_optimized": stats_row["voice_optimized_count"],
                    "total_usage": stats_row["total_usage"],
                    "overall_avg_score": round(stats_row["overall_avg_score"] or 0, 2)
                },
                "skill_breakdown": skill_breakdown,
                "difficulty_breakdown": difficulty_breakdown,
                "performance_stats": self.stats,
                "recent_activity": recent_activity,
                "intelligent_selection": True,
                "cache_status": {
                    "cached_questions": len(self.question_cache),
                    "last_update": self.last_cache_update.isoformat() if self.last_cache_update else None
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get question bank status: {e}")
            return {
                "initialized": self.initialized,
                "error": str(e)
            }
    
    async def get_questions_by_criteria(
        self,
        skill_category: str = None,
        difficulty: str = None,
        question_type: str = None,
        voice_optimized: bool = None,
        limit: int = 10
    ) -> List[Question]:
        """Get questions matching specific criteria"""
        
        try:
            cursor = self.db_connection.cursor()
            
            where_clauses = []
            params = []
            
            if skill_category:
                where_clauses.append("skill_category = ?")
                params.append(skill_category)
            
            if difficulty:
                where_clauses.append("difficulty = ?")
                params.append(difficulty)
            
            if question_type:
                where_clauses.append("type = ?")
                params.append(question_type)
            
            if voice_optimized is not None:
                where_clauses.append("voice_optimized = ?")
                params.append(1 if voice_optimized else 0)
            
            where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
            
            query = f"""
                SELECT * FROM questions 
                {where_clause}
                ORDER BY usage_count ASC, created_at DESC
                LIMIT ?
            """
            
            params.append(limit)
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [self._create_question_object(dict(row)) for row in rows]
            
        except Exception as e:
            self.logger.error(f"Failed to get questions by criteria: {e}")
            return []
    
    async def add_custom_question(
        self,
        text: str,
        skill_category: str,
        difficulty: str = "intermediate",
        question_type: str = "free_text",
        expected_keywords: List[str] = None,
        voice_optimized: bool = True,
        estimated_time: int = 5
    ) -> str:
        """Add a custom question to the bank"""
        
        try:
            question_id = f"custom_{uuid.uuid4().hex[:12]}"
            
            question_data = {
                "id": question_id,
                "text": text,
                "type": question_type,
                "skill_category": skill_category,
                "difficulty": difficulty,
                "estimated_time_minutes": estimated_time,
                "expected_keywords": expected_keywords or [],
                "voice_optimized": voice_optimized
            }
            
            await self._insert_question(question_data)
            await self._update_question_cache()
            
            self.logger.info(f"✅ Added custom question: {question_id}")
            return question_id
            
        except Exception as e:
            self.logger.error(f"Failed to add custom question: {e}")
            raise Exception(f"Failed to add question: {e}")
    
    async def update_question(
        self,
        question_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update an existing question"""
        
        try:
            cursor = self.db_connection.cursor()
            
            # Build update query
            set_clauses = []
            params = []
            
            for field, value in updates.items():
                if field in ["text", "type", "skill_category", "difficulty", "estimated_time_minutes", "voice_optimized"]:
                    set_clauses.append(f"{field} = ?")
                    params.append(value)
                elif field == "expected_keywords":
                    set_clauses.append("expected_keywords = ?")
                    params.append(json.dumps(value))
            
            if not set_clauses:
                return False
            
            set_clauses.append("updated_at = ?")
            params.append(datetime.utcnow().isoformat())
            params.append(question_id)
            
            query = f"""
                UPDATE questions 
                SET {', '.join(set_clauses)}
                WHERE id = ?
            """
            
            cursor.execute(query, params)
            self.db_connection.commit()
            
            await self._update_question_cache()
            
            self.logger.info(f"✅ Updated question: {question_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update question: {e}")
            return False
    
    async def get_question_analytics(
        self,
        question_id: str = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get analytics for questions"""
        
        try:
            cursor = self.db_connection.cursor()
            
            # Date filter
            since_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            if question_id:
                # Analytics for specific question
                cursor.execute("""
                    SELECT 
                        COUNT(*) as response_count,
                        AVG(evaluation_score) as avg_score,
                        MIN(evaluation_score) as min_score,
                        MAX(evaluation_score) as max_score,
                        AVG(time_taken_seconds) as avg_time_taken
                    FROM question_responses 
                    WHERE question_id = ? AND created_at >= ?
                """, (question_id, since_date))
                
                stats = cursor.fetchone()
                
                return {
                    "question_id": question_id,
                    "period_days": days,
                    "response_count": stats["response_count"],
                    "avg_score": round(stats["avg_score"] or 0, 2),
                    "min_score": stats["min_score"],
                    "max_score": stats["max_score"],
                    "avg_time_taken": round(stats["avg_time_taken"] or 0, 1)
                }
            else:
                # Overall analytics
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_responses,
                        COUNT(DISTINCT question_id) as questions_used,
                        COUNT(DISTINCT session_id) as unique_sessions,
                        AVG(evaluation_score) as overall_avg_score
                    FROM question_responses 
                    WHERE created_at >= ?
                """, (since_date,))
                
                overall_stats = cursor.fetchone()
                
                # Top performing questions
                cursor.execute("""
                    SELECT 
                        q.id, q.text, q.skill_category, 
                        COUNT(qr.id) as usage_count,
                        AVG(qr.evaluation_score) as avg_score
                    FROM questions q
                    JOIN question_responses qr ON q.id = qr.question_id
                    WHERE qr.created_at >= ?
                    GROUP BY q.id
                    ORDER BY avg_score DESC
                    LIMIT 5
                """, (since_date,))
                
                top_questions = [dict(row) for row in cursor.fetchall()]
                
                return {
                    "period_days": days,
                    "overall_stats": dict(overall_stats),
                    "top_performing_questions": top_questions
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get question analytics: {e}")
            return {"error": str(e)}
    
    async def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old response data"""
        
        try:
            cursor = self.db_connection.cursor()
            
            cutoff_date = (datetime.utcnow() - timedelta(days=days_to_keep)).isoformat()
            
            cursor.execute("""
                DELETE FROM question_responses 
                WHERE created_at < ?
            """, (cutoff_date,))
            
            cursor.execute("""
                DELETE FROM question_analytics 
                WHERE recorded_at < ?
            """, (cutoff_date,))
            
            deleted_responses = cursor.rowcount
            self.db_connection.commit()
            
            self.logger.info(f"✅ Cleaned up {deleted_responses} old records")
            return deleted_responses
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")
            return 0
    
    async def export_questions(self, format: str = "json") -> str:
        """Export questions to file"""
        
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT * FROM questions ORDER BY skill_category, difficulty")
            
            questions = []
            for row in cursor.fetchall():
                question_dict = dict(row)
                # Parse JSON fields
                question_dict["expected_keywords"] = json.loads(question_dict.get("expected_keywords", "[]"))
                questions.append(question_dict)
            
            # Export to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if format.lower() == "json":
                filename = f"questions_export_{timestamp}.json"
                with open(filename, 'w') as f:
                    json.dump(questions, f, indent=2, default=str)
            else:
                # CSV format
                import csv
                filename = f"questions_export_{timestamp}.csv"
                with open(filename, 'w', newline='') as f:
                    if questions:
                        writer = csv.DictWriter(f, fieldnames=questions[0].keys())
                        writer.writeheader()
                        writer.writerows(questions)
            
            self.logger.info(f"✅ Exported {len(questions)} questions to {filename}")
            return filename
            
        except Exception as e:
            self.logger.error(f"Failed to export questions: {e}")
            raise Exception(f"Export failed: {e}")
    
    def close(self):
        """Close database connection"""
        
        if self.db_connection:
            self.db_connection.close()
            self.db_connection = None
            self.initialized = False

# =============================================================================
# QUESTION BANK FACTORY
# =============================================================================

class QuestionBankFactory:
    """Factory for creating question bank instances"""
    
    @staticmethod
    async def create_enhanced_question_bank(
        db_path: str = "question_bank.db",
        claude_client=None,
        initialize: bool = True
    ) -> EnhancedQuestionBankManager:
        """Create enhanced question bank"""
        
        try:
            question_bank = EnhancedQuestionBankManager(db_path, claude_client)
            
            if initialize:
                await question_bank.initialize(populate_sample_data=True)
            
            logger.info(f"✅ Enhanced question bank created: {db_path}")
            return question_bank
            
        except Exception as e:
            logger.error(f"Failed to create question bank: {e}")
            raise Exception(f"Question bank creation failed: {e}")
    
    @staticmethod
    async def create_voice_optimized_bank(
        db_path: str = "voice_questions.db",
        claude_client=None
    ) -> EnhancedQuestionBankManager:
        """Create voice-optimized question bank"""
        
        question_bank = await QuestionBankFactory.create_enhanced_question_bank(
            db_path=db_path,
            claude_client=claude_client,
            initialize=True
        )
        
        # Additional voice optimization could be added here
        logger.info(f"✅ Voice-optimized question bank created")
        return question_bank
    
    @staticmethod
    async def create_development_bank() -> EnhancedQuestionBankManager:
        """Create development question bank"""
        
        return await QuestionBankFactory.create_enhanced_question_bank(
            db_path="dev_question_bank.db",
            claude_client=None,
            initialize=True
        )

# =============================================================================
# TESTING AND EXAMPLES
# =============================================================================

async def test_question_bank():
    """Test the enhanced question bank"""
    
    print("📚 Testing Enhanced Question Bank")
    print("=" * 50)
    
    try:
        # Create question bank
        print("📦 Creating question bank...")
        question_bank = await QuestionBankFactory.create_development_bank()
        
        # Get status
        status = await question_bank.get_question_bank_status()
        if status["initialized"]:
            stats = status["question_statistics"]
            print(f"✅ Question bank initialized")
            print(f"   Total questions: {stats['total_questions']}")
            print(f"   Skill categories: {stats['skill_categories']}")
            print(f"   Voice optimized: {stats['voice_optimized']}")
        
        # Test question selection strategies
        print("\n🎯 Testing question selection...")
        
        strategies = ["sequential", "adaptive", "adaptive_voice", "skill_based"]
        
        for strategy in strategies:
            question = await question_bank.get_question(strategy=strategy)
            if question:
                print(f"✅ {strategy}: {question.text[:50]}...")
            else:
                print(f"❌ {strategy}: No question returned")
        
        # Test session-based selection
        print("\n📝 Testing session-based selection...")
        session_state = {
            "session_id": "test_session",
            "questions_asked": [],
            "evaluations": [],
            "skills_covered": {}
        }
        
        # Get a few questions
        for i in range(3):
            question = await question_bank.get_question(
                strategy="adaptive_voice",
                session_state=session_state
            )
            
            if question:
                print(f"✅ Question {i+1}: {question.skill_category} - {question.difficulty}")
                
                # Simulate response
                session_state["questions_asked"].append(question.id)
                session_state["evaluations"].append({"score": 3.5})
                session_state["skills_covered"][question.skill_category] = 1
                
                # Record response
                await question_bank.record_question_response(
                    question_id=question.id,
                    session_id="test_session",
                    evaluation={"score": 3.5, "reasoning": "Good test response"},
                    response_text="Test response"
                )
            else:
                print(f"❌ Question {i+1}: None returned")
        
        # Test analytics
        print("\n📊 Testing analytics...")
        analytics = await question_bank.get_question_analytics()
        if "overall_stats" in analytics:
            print(f"✅ Analytics: {analytics['overall_stats']['total_responses']} total responses")
        
        # Clean up
        question_bank.close()
        
        print("\n✅ Question bank test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("📚 Enhanced Question Bank with Database Support")
    print("=" * 70)
    print("✅ Features:")
    print("  • SQLite database storage")
    print("  • Intelligent question selection strategies")
    print("  • Voice-optimized questions")
    print("  • Performance tracking and analytics")
    print("  • Session-based adaptive selection")
    print("  • Question response recording")
    print("  • Comprehensive statistics")
    
    # Run test
    success = asyncio.run(test_question_bank())
    print(f"\n{'🎉 All tests passed!' if success else '❌ Some tests failed'}")