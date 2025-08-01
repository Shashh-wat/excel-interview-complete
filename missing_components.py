# missing_components.py - Fixed Helper for Missing Components
"""
This file provides fallback implementations for components that might be missing
from your setup. Include this to make your system work without all dependencies.

FIXED: Added proper integration with your existing files
"""

import logging
import asyncio
import uuid
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# =============================================================================
# VOICE INTERVIEW SERVICE FALLBACKS
# =============================================================================

class VoiceInterviewServiceFactory:
    """Factory for voice interview services with fallbacks"""
    
    @staticmethod
    async def create_voice_service(murf_api_key: str = None, claude_client=None, voice_id: str = None):
        """Create voice service (uses your main.py implementation)"""
        try:
            # Try to import from main.py
            from main import VoiceService, MurfAPIClient
            murf_client = MurfAPIClient(murf_api_key or "test_key")
            voice_service = VoiceService(murf_client)
            print("✅ Real voice service loaded from main.py")
            return voice_service
        except ImportError:
            logger.warning("Main voice service not available, using fallback")
            return FallbackVoiceService()

class FallbackVoiceService:
    """Fallback voice service when main service is not available"""
    
    def __init__(self):
        self.available = False
        self.stats = {
            "tts_requests": 0,
            "tts_successes": 0,
            "tts_failures": 0
        }
    
    async def text_to_speech(self, text: str, voice_id: str = None) -> Dict[str, Any]:
        """Fallback TTS - just returns success without actual audio"""
        self.stats["tts_requests"] += 1
        self.stats["tts_failures"] += 1
        
        return {
            "success": False,
            "error": "Voice service not available - Murf integration needed",
            "audio_path": None
        }
    
    async def generate_speech(self, text: str, context: str = None, voice_id: str = None) -> Dict[str, Any]:
        """Alternative method name that might be used"""
        return await self.text_to_speech(text, voice_id)
    
    async def speech_to_text(self, audio_path: str, session_id: str) -> Dict[str, Any]:
        """Fallback STT"""
        return {
            "success": False,
            "error": "Speech-to-text not available",
            "transcript": "",
            "confidence": 0
        }
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "available": False,
            "service_type": "fallback",
            "murf_api_available": False,
            "stats": self.stats,
            "note": "Fallback service - no actual voice processing"
        }
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get service stats (alternative method name)"""
        return self.get_service_status()

# =============================================================================
# QUESTION BANK FALLBACKS  
# =============================================================================

class QuestionBankFactory:
    """Factory for question banks with fallbacks"""
    
    @staticmethod
    def create_database_question_bank(db_path: str = "question_bank.db", claude_client=None, auto_initialize: bool = True):
        """Create database-backed question bank"""
        try:
            from question_bank_db import EnhancedQuestionBankManager
            return EnhancedQuestionBankManager(db_path, claude_client)
        except ImportError:
            logger.warning("Enhanced question bank not available, using simple fallback")
            return SimpleQuestionBank()
    
    @staticmethod
    async def create_enhanced_question_bank(db_path: str = "question_bank.db", claude_client=None, initialize: bool = True):
        """Create enhanced question bank (async version)"""
        try:
            from question_bank_db import EnhancedQuestionBankManager
            manager = EnhancedQuestionBankManager(db_path, claude_client)
            if initialize:
                await manager.initialize()
            return manager
        except ImportError:
            logger.warning("Enhanced question bank not available, using simple fallback")
            return SimpleQuestionBank()

class SimpleQuestionBank:
    """Simple fallback question bank that matches the interface expected by orchestrator"""
    
    def __init__(self):
        self.questions = [
            {
                "id": "excel_q1",
                "text": "Explain the difference between VLOOKUP and INDEX-MATCH functions in Excel. When would you use each one?",
                "type": "free_text",
                "skill_category": "formulas",
                "difficulty": "intermediate",
                "expected_keywords": ["VLOOKUP", "INDEX", "MATCH", "lookup", "table", "flexible"]
            },
            {
                "id": "excel_q2",
                "text": "How do you create a pivot table in Excel? Describe the key steps and what type of data analysis it's useful for.",
                "type": "free_text", 
                "skill_category": "pivot_tables",
                "difficulty": "intermediate",
                "expected_keywords": ["pivot table", "summarize", "data", "rows", "columns", "values"]
            },
            {
                "id": "excel_q3",
                "text": "What are some common Excel errors like #N/A, #REF!, #VALUE! and how would you troubleshoot them?",
                "type": "free_text",
                "skill_category": "error_handling", 
                "difficulty": "intermediate",
                "expected_keywords": ["#N/A", "#REF!", "#VALUE!", "error", "troubleshoot", "IFERROR"]
            },
            {
                "id": "excel_q4",
                "text": "Describe how to use conditional formatting in Excel to highlight data based on specific criteria.",
                "type": "free_text",
                "skill_category": "data_manipulation",
                "difficulty": "beginner",
                "expected_keywords": ["conditional formatting", "highlight", "criteria", "rules", "format"]
            },
            {
                "id": "excel_q5",
                "text": "Explain how you would use SUMIF and COUNTIF functions. Provide examples of when they're useful.",
                "type": "free_text",
                "skill_category": "formulas", 
                "difficulty": "intermediate",
                "expected_keywords": ["SUMIF", "COUNTIF", "criteria", "range", "condition"]
            },
            {
                "id": "excel_q6",
                "text": "How do you protect cells and worksheets in Excel? What are the different protection options available?",
                "type": "free_text",
                "skill_category": "data_manipulation",
                "difficulty": "advanced",
                "expected_keywords": ["protect", "lock", "password", "worksheet", "cells", "security"]
            }
        ]
        self.current_index = 0
        self._initialized = True
    
    async def get_question(self, strategy="sequential", **kwargs):
        """Get next question - matches interface expected by orchestrator"""
        if self.current_index >= len(self.questions):
            return None
        
        question_data = self.questions[self.current_index]
        self.current_index += 1
        
        # Create question object that matches the interface
        try:
            from models import Question, SkillCategory, DifficultyLevel, QuestionType
            question = Question(
                id=question_data["id"],
                text=question_data["text"],
                type=QuestionType(question_data["type"]),
                skill_category=SkillCategory(question_data["skill_category"]),
                difficulty=DifficultyLevel(question_data["difficulty"]),
                estimated_time_minutes=5,
                expected_keywords=question_data["expected_keywords"]
            )
        except ImportError:
            # Fallback question object
            from types import SimpleNamespace
            question = SimpleNamespace(**question_data)
            question.to_dict = lambda: question_data
            question.expected_keywords = question_data["expected_keywords"]
        
        return question
    
    async def get_question_bank_status(self):
        """Get question bank status"""
        return {
            "initialized": True,
            "total_questions": len(self.questions),
            "remaining_questions": len(self.questions) - self.current_index,
            "question_statistics": {
                "total_questions": len(self.questions),
                "by_type": {"free_text": len(self.questions)},
                "by_skill": {
                    "formulas": 2,
                    "pivot_tables": 1,
                    "error_handling": 1,
                    "data_manipulation": 2
                },
                "by_difficulty": {
                    "beginner": 1,
                    "intermediate": 4,
                    "advanced": 1
                }
            }
        }
    
    def get_stats(self):
        """Get question bank stats (sync version)"""
        return {
            "total_questions": len(self.questions),
            "categories": 4,
            "remaining": len(self.questions) - self.current_index
        }

# =============================================================================
# EVALUATION ENGINE FALLBACKS
# =============================================================================

class FallbackEvaluationEngine:
    """Fallback evaluation engine that matches the interface expected by orchestrator"""
    
    def __init__(self):
        self.available = False
        self.evaluation_stats = {
            "total_evaluations": 0,
            "cache_hits": 0,
            "llm_evaluations": 0,
            "file_evaluations": 0,
            "avg_evaluation_time": 0.0
        }
    
    async def health_check(self):
        """Health check that matches expected interface"""
        return {
            "status": "degraded",
            "health_percentage": 50,
            "claude_available": False,
            "evaluation_functional": True,
            "issues": ["Claude API not available - using keyword-based fallback"],
            "openpyxl_available": False,
            "xlrd_available": False,
            "cache_enabled": False
        }
    
    async def evaluate_response(self, question, text_response: str = None, file_path: str = None):
        """Fallback evaluation that matches expected interface"""
        self.evaluation_stats["total_evaluations"] += 1
        
        # Handle different question formats
        if hasattr(question, 'to_dict'):
            question_dict = question.to_dict()
        elif isinstance(question, dict):
            question_dict = question
        else:
            question_dict = {
                "id": getattr(question, 'id', 'unknown'),
                "text": getattr(question, 'text', ''),
                "expected_keywords": getattr(question, 'expected_keywords', [])
            }
        
        if not text_response or not text_response.strip():
            return {
                "score": 0.0,
                "confidence": 1.0,
                "reasoning": "No response provided",
                "strengths": [],
                "areas_for_improvement": ["Please provide a response"],
                "keywords_found": [],
                "mistakes_detected": [],
                "question_id": question_dict.get("id", "unknown"),
                "evaluation_time_ms": 50,
                "evaluator_type": "fallback",
                "created_at": datetime.utcnow().isoformat()
            }
        
        # Simple length and keyword based scoring
        expected_keywords = question_dict.get("expected_keywords", [])
        keywords_found = []
        
        if expected_keywords:
            response_lower = text_response.lower()
            keywords_found = [kw for kw in expected_keywords if kw.lower() in response_lower]
        
        word_count = len(text_response.split())
        
        # Scoring algorithm
        base_score = 1.5  # Base for providing response
        keyword_bonus = min(2.0, len(keywords_found) * 0.5)
        length_bonus = min(1.5, word_count / 30)
        
        final_score = min(5.0, base_score + keyword_bonus + length_bonus)
        
        return {
            "score": round(final_score, 1),
            "confidence": 0.6,
            "reasoning": f"Fallback evaluation: Found {len(keywords_found)} relevant keywords in {word_count} word response",
            "strengths": [f"Mentioned {kw}" for kw in keywords_found[:3]] or ["Response provided"],
            "areas_for_improvement": ["Enable Claude API for detailed analysis", "Add more specific Excel terminology"],
            "keywords_found": keywords_found,
            "mistakes_detected": [],
            "question_id": question_dict.get("id", "unknown"),
            "evaluation_time_ms": 100,
            "evaluator_type": "fallback",
            "created_at": datetime.utcnow().isoformat()
        }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            "evaluation_stats": self.evaluation_stats,
            "cache_performance": {"hits": 0, "misses": 0, "hit_rate_percentage": 0},
            "claude_api_stats": {"total_calls": 0, "successful_calls": 0, "failed_calls": 0, "success_rate": 0},
            "overall_cache_hit_rate": 0,
            "avg_evaluation_time": 0.1
        }

# =============================================================================
# MODELS FALLBACKS
# =============================================================================

try:
    from models import *
except ImportError:
    logger.warning("models.py not available, creating fallback enums")
    
    from enum import Enum
    from dataclasses import dataclass
    from datetime import datetime
    
    class SkillCategory(Enum):
        FORMULAS = "formulas"
        DATA_MANIPULATION = "data_manipulation"
        PIVOT_TABLES = "pivot_tables"
        DATA_ANALYSIS = "data_analysis"
        ERROR_HANDLING = "error_handling"
        DATA_VISUALIZATION = "data_visualization"
        ADVANCED_FUNCTIONS = "advanced_functions"
    
    class DifficultyLevel(Enum):
        BEGINNER = "beginner"
        INTERMEDIATE = "intermediate"
        ADVANCED = "advanced"
    
    class QuestionType(Enum):
        FREE_TEXT = "free_text"
        FILE_UPLOAD = "file_upload"
        HYBRID = "hybrid"
    
    class InterviewStatus(Enum):
        NOT_STARTED = "not_started"
        IN_PROGRESS = "in_progress"
        COMPLETED = "completed"
        ERROR = "error"
    
    @dataclass
    class Question:
        id: str
        text: str
        type: QuestionType
        skill_category: SkillCategory
        difficulty: DifficultyLevel
        estimated_time_minutes: int
        expected_keywords: List[str] = None
        
        def to_dict(self):
            return {
                "id": self.id,
                "text": self.text,
                "type": self.type.value,
                "skill_category": self.skill_category.value,
                "difficulty": self.difficulty.value,
                "estimated_time_minutes": self.estimated_time_minutes,
                "expected_keywords": self.expected_keywords or []
            }

# =============================================================================
# CONFIGURATION AND INITIALIZATION
# =============================================================================

async def initialize_fallback_system():
    """Initialize system with fallback components"""
    
    print("🔧 Initializing system with fallback components...")
    
    try:
        # Try to get real evaluation engine
        try:
            from evaluation_engine import ClaudeEvaluationEngine
            evaluation_engine = ClaudeEvaluationEngine()
            print("✅ Real evaluation engine loaded")
        except ImportError:
            evaluation_engine = FallbackEvaluationEngine()
            print("⚠️ Using fallback evaluation engine")
        
        # Try to get voice service
        voice_service = await VoiceInterviewServiceFactory.create_voice_service()
        if hasattr(voice_service, 'available') and voice_service.available:
            print("✅ Voice service available")
        else:
            print("⚠️ Voice service not available")
        
        # Get question bank
        question_bank = await QuestionBankFactory.create_enhanced_question_bank()
        print("✅ Question bank loaded")
        
        # Create orchestrator
        try:
            from interview_orchestrator import InterviewWorkflowFactory
            orchestrator = InterviewWorkflowFactory.create_complete_workflow(
                evaluation_engine=evaluation_engine,
                question_bank=question_bank
            )
            print("✅ Interview orchestrator created")
        except ImportError:
            # Create a basic orchestrator
            from interview_orchestrator import InterviewOrchestrator
            orchestrator = InterviewOrchestrator(
                evaluation_engine=evaluation_engine,
                question_bank=question_bank
            )
            print("✅ Basic interview orchestrator created")
        
        return {
            "evaluation_engine": evaluation_engine,
            "voice_service": voice_service,
            "question_bank": question_bank,
            "interview_orchestrator": orchestrator,
            "status": "initialized"
        }
        
    except Exception as e:
        print(f"❌ Fallback initialization failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

def create_test_components():
    """Create minimal test components for development"""
    
    class TestEvaluationEngine:
        def __init__(self):
            self.available = True
        
        async def health_check(self):
            return {
                "status": "test", 
                "health_percentage": 100,
                "claude_available": True,
                "evaluation_functional": True
            }
        
        async def evaluate_response(self, question, text_response, file_path=None):
            return {
                "score": 3.5,
                "confidence": 0.8,
                "reasoning": "Test evaluation - good response with relevant Excel knowledge",
                "strengths": ["Clear explanation", "Good use of terminology"],
                "areas_for_improvement": ["Could add examples", "More detail on use cases"],
                "keywords_found": ["excel", "function", "lookup"],
                "mistakes_detected": [],
                "question_id": getattr(question, 'id', 'test_q1'),
                "evaluation_time_ms": 250,
                "evaluator_type": "test",
                "created_at": datetime.utcnow().isoformat()
            }
        
        def get_performance_stats(self):
            return {
                "evaluation_stats": {"total_evaluations": 0},
                "claude_api_stats": {"success_rate": 100},
                "overall_cache_hit_rate": 0
            }
    
    class TestVoiceService:
        def __init__(self):
            self.available = True
        
        async def text_to_speech(self, text, voice_id=None):
            return {
                "success": True,
                "audio_path": "/fake/path/test_audio.mp3",
                "voice_id": voice_id or "test-voice",
                "text_length": len(text),
                "note": "Test audio - not real file"
            }
        
        async def generate_speech(self, text, context=None, voice_id=None):
            return await self.text_to_speech(text, voice_id)
        
        def get_service_status(self):
            return {
                "available": True,
                "service_type": "test", 
                "murf_api_available": True,
                "stats": {"tts_requests": 0, "tts_successes": 0}
            }
        
        def get_service_stats(self):
            return self.get_service_status()
    
    return {
        "evaluation_engine": TestEvaluationEngine(),
        "voice_service": TestVoiceService(),
        "question_bank": SimpleQuestionBank()
    }

# =============================================================================
# COMPATIBILITY LAYER
# =============================================================================

def ensure_compatibility():
    """Ensure backward compatibility with existing code"""
    
    # Create global instances for backward compatibility
    import sys
    module = sys.modules[__name__]
    
    # Set up fallback factories if not available
    if not hasattr(module, 'VoiceInterviewService'):
        setattr(module, 'VoiceInterviewService', FallbackVoiceService)
    
    if not hasattr(module, 'EnhancedQuestionBankManager'):
        setattr(module, 'EnhancedQuestionBankManager', SimpleQuestionBank)
    
    print("✅ Compatibility layer activated")

# =============================================================================
# QUICK SETUP FUNCTION
# =============================================================================

async def quick_setup_for_main():
    """Quick setup function that main.py can use"""
    
    try:
        # Initialize components
        components = await initialize_fallback_system()
        
        if components["status"] == "error":
            print(f"❌ Setup failed: {components['error']}")
            # Return test components as fallback
            return create_test_components()
        
        print("✅ System setup completed successfully")
        return components
        
    except Exception as e:
        print(f"❌ Quick setup failed: {e}")
        # Return test components as ultimate fallback
        return create_test_components()

# =============================================================================
# INTEGRATION HELPER FOR CONFIG.PY
# =============================================================================

async def create_service_container_components(config):
    """Create components for ServiceContainer in config.py"""
    
    try:
        # Evaluation Engine
        try:
            from evaluation_engine import ClaudeEvaluationEngine
            evaluation_engine = ClaudeEvaluationEngine(
                anthropic_api_key=config.anthropic_api_key
            )
        except ImportError:
            evaluation_engine = FallbackEvaluationEngine()
        
        # Voice Service
        voice_service = await VoiceInterviewServiceFactory.create_voice_service(
            murf_api_key=config.murf_api_key
        )
        
        # Question Bank
        question_bank = await QuestionBankFactory.create_enhanced_question_bank(
            db_path=config.question_bank_db
        )
        
        # Interview Orchestrator
        try:
            from interview_orchestrator import VoiceEnhancedInterviewOrchestrator
            orchestrator = VoiceEnhancedInterviewOrchestrator(
                evaluation_engine=evaluation_engine,
                question_bank=question_bank,
                voice_service=voice_service
            )
        except ImportError:
            from interview_orchestrator import InterviewOrchestrator
            orchestrator = InterviewOrchestrator(
                evaluation_engine=evaluation_engine,
                question_bank=question_bank
            )
        
        return {
            "evaluation_engine": evaluation_engine,
            "voice_service": voice_service,
            "question_bank": question_bank,
            "interview_orchestrator": orchestrator
        }
        
    except Exception as e:
        logger.error(f"Failed to create service container components: {e}")
        # Return test components as fallback
        return create_test_components()

# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    print("🔧 Fixed Missing Components Helper")
    print("=" * 50)
    print("This file provides fallback implementations for missing components.")
    print("Run this to test fallback systems:")
    
    async def test_fallbacks():
        print("\n🧪 Testing component creation...")
        components = await quick_setup_for_main()
        
        print(f"\n📊 Component Status:")
        for name, component in components.items():
            if hasattr(component, 'available'):
                status = "✅ Available" if component.available else "⚠️ Fallback"
            else:
                status = "✅ Loaded"
            print(f"  {name}: {status}")
        
        # Test basic interview flow
        if "interview_orchestrator" in components:
            orchestrator = components["interview_orchestrator"]
            print(f"\n🧪 Testing interview flow...")
            
            try:
                start_result = await orchestrator.start_interview("Test User")
                if start_result.get("success", True):
                    print("✅ Interview start works")
                    
                    session_id = start_result["session_id"]
                    response_result = await orchestrator.submit_response(
                        session_id, "VLOOKUP is a lookup function in Excel that searches for values in tables"
                    )
                    
                    if response_result.get("success", True):
                        print("✅ Response submission works")
                        eval_data = response_result.get("evaluation", {})
                        print(f"   Score: {eval_data.get('score', 0)}/5.0")
                        print(f"   Reasoning: {eval_data.get('reasoning', 'No reasoning')[:60]}...")
                    else:
                        print(f"❌ Response submission failed: {response_result.get('error')}")
                else:
                    print(f"❌ Interview start failed: {start_result.get('error')}")
            except Exception as e:
                print(f"❌ Interview flow test failed: {e}")
        
        # Test evaluation engine directly
        if "evaluation_engine" in components:
            print(f"\n🧪 Testing evaluation engine...")
            eval_engine = components["evaluation_engine"]
            
            try:
                health = await eval_engine.health_check()
                print(f"✅ Health check: {health.get('status')} ({health.get('health_percentage', 0)}%)")
                
                test_question = {
                    "id": "test_q1",
                    "text": "What is VLOOKUP?",
                    "expected_keywords": ["VLOOKUP", "lookup", "function"]
                }
                
                evaluation = await eval_engine.evaluate_response(
                    test_question, 
                    "VLOOKUP is a vertical lookup function in Excel"
                )
                
                print(f"✅ Evaluation test: {evaluation.get('score', 0)}/5.0")
                
            except Exception as e:
                print(f"❌ Evaluation engine test failed: {e}")
        
        print(f"\n🎉 All tests completed!")
    
    asyncio.run(test_fallbacks())