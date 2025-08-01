# main.py - COMPLETE Production-Ready Excel Interview System with Full Voice Integration
import asyncio
import logging
import uuid
import aiofiles
import aiohttp
import os
import tempfile
import json
import shutil
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
# FIXED VOICE SYSTEM
from voice_fix_integration import initialize_working_voice_system

load_dotenv()

# =============================================================================
# COMPLETE MURF API CLIENT
# =============================================================================

class MurfAPIClient:
    """WORKING Murf API client that actually works"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.murf.ai/v1"
        self.available = bool(api_key and api_key != "test_key")
        self.default_voice_id = "en-US-cooper"  # YOUR WORKING VOICE ID
        self.logger = logging.getLogger(__name__)
        
        # Ensure voice cache directory exists
        self.cache_dir = Path("voice_cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        # API stats tracking
        self.api_stats = {
            "requests_made": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_audio_files": 0,
            "total_characters_processed": 0
        }
        
    async def text_to_speech(self, text: str, voice_id: str = None) -> Dict[str, Any]:
        """Generate speech with working headers and voice ID"""
        
        if not self.available:
            return {
                "success": False, 
                "error": "Murf API not configured",
                "audio_path": None,
                "audio_url": None
            }
        
        if not text or not text.strip():
            return {
                "success": False,
                "error": "No text provided",
                "audio_path": None,
                "audio_url": None
            }
        
        # Clean and limit text
        clean_text = text.strip()[:5000]
        
        self.api_stats["requests_made"] += 1
        self.api_stats["total_characters_processed"] += len(clean_text)
        
        try:
            payload = {
                "voiceId": voice_id or self.default_voice_id,
                "text": clean_text,
                "audioFormat": "MP3",
                "sampleRate": 24000
            }
            
            headers = {
                "api-key": self.api_key,  # CORRECT HEADER FORMAT
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/speech/generate", 
                    json=payload, 
                    headers=headers, 
                    timeout=aiohttp.ClientTimeout(total=45)
                ) as response:
                    
                    if response.status == 200:
                        response_data = await response.json()
                        
                        if "audioFile" in response_data:
                            # Download and store audio file
                            audio_file_url = response_data["audioFile"]
                            local_audio_path = await self._download_audio(audio_file_url)
                            
                            if local_audio_path:
                                # Generate public URL for frontend
                                audio_filename = Path(local_audio_path).name
                                public_audio_url = f"/audio/{audio_filename}"
                                
                                self.api_stats["successful_requests"] += 1
                                self.api_stats["total_audio_files"] += 1
                                
                                return {
                                    "success": True,
                                    "audio_path": local_audio_path,
                                    "audio_url": public_audio_url,
                                    "voice_id": voice_id or self.default_voice_id,
                                    "text_length": len(clean_text),
                                    "audio_filename": audio_filename
                                }
                            else:
                                self.api_stats["failed_requests"] += 1
                                return {
                                    "success": False,
                                    "error": "Failed to download audio file",
                                    "audio_path": None,
                                    "audio_url": None
                                }
                        else:
                            self.api_stats["failed_requests"] += 1
                            return {
                                "success": False,
                                "error": "No audio file in Murf response",
                                "audio_path": None,
                                "audio_url": None
                            }
                    else:
                        self.api_stats["failed_requests"] += 1
                        error_text = await response.text()
                        self.logger.error(f"Murf API error {response.status}: {error_text}")
                        return {
                            "success": False,
                            "error": f"Murf API error: {response.status} - {error_text}",
                            "audio_path": None,
                            "audio_url": None
                        }
                        
        except asyncio.TimeoutError:
            self.api_stats["failed_requests"] += 1
            self.logger.error("Murf API timeout")
            return {
                "success": False,
                "error": "Murf API timeout - request took too long",
                "audio_path": None,
                "audio_url": None
            }
        except Exception as e:
            self.api_stats["failed_requests"] += 1
            self.logger.error(f"Murf API failed: {e}")
            return {
                "success": False,
                "error": f"Murf API error: {str(e)}",
                "audio_path": None,
                "audio_url": None
            }
    
    async def _download_audio(self, audio_url: str) -> str:
        """Download audio file and store locally"""
        
        try:
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"murf_audio_{timestamp}_{uuid.uuid4().hex[:8]}.mp3"
            file_path = self.cache_dir / filename
            
            # Download file with timeout
            async with aiohttp.ClientSession() as session:
                async with session.get(audio_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        async with aiofiles.open(file_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                        
                        self.logger.info(f"✅ Audio downloaded: {file_path}")
                        return str(file_path)
                    else:
                        raise Exception(f"Download failed with status {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Audio download failed: {e}")
            return None
    
    def get_default_voices(self) -> List[Dict[str, str]]:
        """Get available Murf voices"""
        return [
            {"id": "en-US-cooper", "name": "Cooper", "language": "English (US)", "gender": "Male", "description": "Professional, clear"},
            {"id": "en-US-imani", "name": "Imani", "language": "English (US)", "gender": "Female", "description": "Warm, engaging"},
            {"id": "en-UK-hazel", "name": "Hazel", "language": "English (UK)", "gender": "Female", "description": "Sophisticated, British"},
        ]
    
    def get_api_stats(self) -> Dict[str, Any]:
        """Get API usage statistics"""
        success_rate = 0
        if self.api_stats["requests_made"] > 0:
            success_rate = (self.api_stats["successful_requests"] / self.api_stats["requests_made"]) * 100
        
        return {
            "requests_made": self.api_stats["requests_made"],
            "successful_requests": self.api_stats["successful_requests"],
            "failed_requests": self.api_stats["failed_requests"],
            "success_rate_percentage": round(success_rate, 2),
            "total_audio_files": self.api_stats["total_audio_files"],
            "total_characters_processed": self.api_stats["total_characters_processed"],
            "cache_files_count": len(list(self.cache_dir.glob("*.mp3"))) if self.cache_dir.exists() else 0
        }
class VoiceService:
    """Complete voice service with comprehensive functionality"""
    
    def __init__(self, murf_client: MurfAPIClient):
        self.murf_client = murf_client
        self.available = murf_client.available
        self.logger = logging.getLogger(__name__)
        
        # Service stats
        self.stats = {
            "tts_requests": 0, 
            "tts_successes": 0, 
            "tts_failures": 0,
            "total_audio_duration_seconds": 0,
            "cache_hits": 0,
            "service_start_time": datetime.utcnow()
        }
        
        # Simple cache for repeated requests
        self.text_cache = {}
        
    async def text_to_speech(self, text: str, voice_id: str = None) -> Dict[str, Any]:
        """Enhanced text-to-speech with caching and stats"""
        
        self.stats["tts_requests"] += 1
        
        # Check cache first
        cache_key = f"{text[:100]}_{voice_id or 'default'}"
        if cache_key in self.text_cache:
            self.stats["cache_hits"] += 1
            cached_result = self.text_cache[cache_key]
            # Check if cached file still exists
            if cached_result.get("audio_path") and Path(cached_result["audio_path"]).exists():
                return cached_result
            else:
                # Remove invalid cache entry
                del self.text_cache[cache_key]
        
        try:
            result = await self.murf_client.text_to_speech(text=text, voice_id=voice_id)
            
            if result["success"]:
                self.stats["tts_successes"] += 1
                
                # Estimate audio duration (rough calculation)
                estimated_duration = len(text.split()) * 0.6  # ~0.6 seconds per word
                self.stats["total_audio_duration_seconds"] += estimated_duration
                
                # Cache successful result
                self.text_cache[cache_key] = result.copy()
                
                # Limit cache size
                if len(self.text_cache) > 100:
                    # Remove oldest entries
                    oldest_key = next(iter(self.text_cache))
                    del self.text_cache[oldest_key]
                
            else:
                self.stats["tts_failures"] += 1
                
            return result
            
        except Exception as e:
            self.stats["tts_failures"] += 1
            self.logger.error(f"Voice service error: {e}")
            return {
                "success": False, 
                "error": str(e), 
                "audio_path": None,
                "audio_url": None
            }
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get comprehensive service statistics"""
        
        total_requests = self.stats["tts_requests"]
        success_rate = (self.stats["tts_successes"] / max(total_requests, 1)) * 100
        cache_hit_rate = (self.stats["cache_hits"] / max(total_requests, 1)) * 100
        
        uptime_seconds = (datetime.utcnow() - self.stats["service_start_time"]).total_seconds()
        
        return {
            "service_type": "murf_tts",
            "available": self.available,
            "uptime_hours": round(uptime_seconds / 3600, 2),
            "stats": self.stats,
            "success_rate_percentage": round(success_rate, 2),
            "cache_hit_rate_percentage": round(cache_hit_rate, 2),
            "estimated_audio_duration_minutes": round(self.stats["total_audio_duration_seconds"] / 60, 2),
            "cache_size": len(self.text_cache),
            "murf_api_stats": self.murf_client.get_api_stats()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check voice service health"""
        
        try:
            if not self.available:
                return {
                    "healthy": False,
                    "error": "Murf API key not configured",
                    "available": False
                }
            
            # Test with short text
            test_result = await self.text_to_speech("Health check test", "en-US-sarah")
            
            return {
                "healthy": test_result.get("success", False),
                "available": self.available,
                "test_result": test_result.get("success", False),
                "error": test_result.get("error") if not test_result.get("success") else None,
                "murf_api_configured": self.murf_client.available
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "available": False
            }

# =============================================================================
# COMPLETE QUESTION BANK
# =============================================================================

class QuestionBank:
    """Complete question bank with comprehensive Excel questions"""
    
    def __init__(self):
        self.questions = [
            {
                "id": "q1",
                "text": "Explain the difference between VLOOKUP and INDEX-MATCH functions in Excel. When would you use each one?",
                "type": "free_text",
                "skill_category": "formulas",
                "difficulty": "intermediate",
                "expected_keywords": ["VLOOKUP", "INDEX", "MATCH", "lookup", "table", "flexible", "array"],
                "estimated_time_minutes": 3
            },
            {
                "id": "q2",
                "text": "How do you create a pivot table in Excel? Describe the key steps and benefits for data analysis.",
                "type": "free_text",
                "skill_category": "pivot_tables", 
                "difficulty": "intermediate",
                "expected_keywords": ["pivot table", "summarize", "data", "rows", "columns", "values", "filter"],
                "estimated_time_minutes": 4
            },
            {
                "id": "q3",
                "text": "What are common Excel errors like hash N A, hash REF, hash VALUE and how do you troubleshoot and fix them?",
                "type": "free_text",
                "skill_category": "error_handling",
                "difficulty": "intermediate", 
                "expected_keywords": ["#N/A", "#REF!", "#VALUE!", "IFERROR", "troubleshoot", "debug"],
                "estimated_time_minutes": 3
            },
            {
                "id": "q4",
                "text": "How do you use conditional formatting to highlight data based on specific criteria in Excel?",
                "type": "free_text",
                "skill_category": "data_manipulation",
                "difficulty": "beginner",
                "expected_keywords": ["conditional formatting", "highlight", "criteria", "rules", "format"],
                "estimated_time_minutes": 2
            },
            {
                "id": "q5",
                "text": "Explain SUMIF and COUNTIF functions with practical examples of when you would use them.",
                "type": "free_text",
                "skill_category": "formulas",
                "difficulty": "intermediate",
                "expected_keywords": ["SUMIF", "COUNTIF", "criteria", "range", "condition", "aggregate"],
                "estimated_time_minutes": 3
            },
            {
                "id": "q6",
                "text": "How do you protect cells and worksheets in Excel? What are the different protection options available?",
                "type": "free_text",
                "skill_category": "data_manipulation",
                "difficulty": "advanced",
                "expected_keywords": ["protect", "lock", "password", "worksheet", "cells", "security"],
                "estimated_time_minutes": 4
            },
            {
                "id": "q7",
                "text": "What is the difference between absolute and relative cell references? Give examples of when to use each type.",
                "type": "free_text",
                "skill_category": "formulas",
                "difficulty": "beginner", 
                "expected_keywords": ["absolute", "relative", "reference", "$", "copy", "formula"],
                "estimated_time_minutes": 2
            },
            {
                "id": "q8",
                "text": "Describe how to create different types of charts in Excel and when you would use each chart type.",
                "type": "free_text",
                "skill_category": "data_manipulation",
                "difficulty": "intermediate",
                "expected_keywords": ["chart", "graph", "bar", "line", "pie", "visualization"],
                "estimated_time_minutes": 3
            }
        ]
        self.current_index = 0
    
    def get_question(self) -> Optional[Dict]:
        """Get next question with enhanced data"""
        if self.current_index >= len(self.questions):
            return None
        
        question = self.questions[self.current_index].copy()
        self.current_index += 1
        return question
    
    def reset(self):
        """Reset question bank"""
        self.current_index = 0
    
    def get_status(self) -> Dict[str, Any]:
        """Get question bank status"""
        return {
            "total_questions": len(self.questions),
            "current_index": self.current_index,
            "remaining_questions": len(self.questions) - self.current_index,
            "categories": list(set(q["skill_category"] for q in self.questions)),
            "difficulty_levels": list(set(q["difficulty"] for q in self.questions))
        }

# =============================================================================
# COMPLETE EVALUATION ENGINE
# =============================================================================

class EvaluationEngine:
    """Complete evaluation engine with enhanced fallback evaluation"""
    
    def __init__(self, anthropic_api_key: str = None):
        self.anthropic_api_key = anthropic_api_key
        self.available = bool(anthropic_api_key and anthropic_api_key != "test_key")
        self.logger = logging.getLogger(__name__)
        
        # Evaluation stats
        self.stats = {
            "evaluations_performed": 0,
            "claude_evaluations": 0,
            "fallback_evaluations": 0,
            "average_score": 0.0
        }
        
        # Initialize Claude client if available
        self.claude_client = None
        if self.available:
            try:
                import anthropic
                self.claude_client = anthropic.AsyncAnthropic(api_key=anthropic_api_key)
                self.logger.info("✅ Claude client initialized")
            except Exception as e:
                self.logger.warning(f"Claude client initialization failed: {e}")
                self.available = False
        
    async def evaluate_response(self, question: Dict, response_text: str, file_path: str = None) -> Dict[str, Any]:
        """Complete response evaluation with Claude integration"""
        
        self.stats["evaluations_performed"] += 1
        
        if not response_text or not response_text.strip():
            return {
                "score": 0.0,
                "confidence": 1.0,
                "reasoning": "No response provided",
                "strengths": [],
                "areas_for_improvement": ["Please provide a response"],
                "keywords_found": [],
                "mistakes_detected": []
            }
        
        # Try Claude evaluation first
        if self.available and self.claude_client:
            try:
                evaluation = await self._claude_evaluation(question, response_text)
                self.stats["claude_evaluations"] += 1
                self._update_average_score(evaluation.get("score", 0))
                return evaluation
            except Exception as e:
                self.logger.warning(f"Claude evaluation failed: {e}")
        
        # Fallback evaluation
        self.stats["fallback_evaluations"] += 1
        evaluation = self._enhanced_fallback_evaluation(question, response_text)
        self._update_average_score(evaluation.get("score", 0))
        return evaluation
    
    async def _claude_evaluation(self, question: Dict, response_text: str) -> Dict[str, Any]:
        """Enhanced Claude-based evaluation"""
        
        question_text = question.get('text', '')
        expected_keywords = question.get('expected_keywords', [])
        difficulty = question.get('difficulty', 'intermediate')
        skill_category = question.get('skill_category', 'general')
        
        prompt = f"""You are an expert Excel interviewer evaluating a candidate's response.

QUESTION: {question_text}

SKILL CATEGORY: {skill_category}
DIFFICULTY: {difficulty}
EXPECTED KEYWORDS: {', '.join(expected_keywords) if expected_keywords else 'N/A'}

CANDIDATE RESPONSE:
{response_text}

Evaluate this response on a scale of 0-5 points based on:
- Technical accuracy and correctness (0-2 points)
- Depth of understanding and explanation (0-2 points)
- Use of appropriate Excel terminology (0-1 point)

Consider the difficulty level when scoring. Advanced questions require more sophisticated answers.

Respond with ONLY valid JSON in this exact format:
{{
  "score": 3.5,
  "confidence": 0.9,
  "reasoning": "Detailed explanation of the score",
  "strengths": ["Specific strength 1", "Specific strength 2"],
  "areas_for_improvement": ["Specific area 1", "Specific area 2"],
  "keywords_found": ["keyword1", "keyword2"],
  "mistakes_detected": ["mistake1", "mistake2"]
}}"""

        try:
            response = await self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text
            
            # Parse JSON response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_content = response_text[json_start:json_end]
                parsed = json.loads(json_content)
                
                return {
                    "score": float(parsed.get("score", 2.5)),
                    "confidence": float(parsed.get("confidence", 0.8)),
                    "reasoning": str(parsed.get("reasoning", "Claude evaluation completed")),
                    "strengths": list(parsed.get("strengths", ["Response provided"])),
                    "areas_for_improvement": list(parsed.get("areas_for_improvement", ["Could be more detailed"])),
                    "keywords_found": list(parsed.get("keywords_found", [])),
                    "mistakes_detected": list(parsed.get("mistakes_detected", [])),
                    "evaluation_method": "claude_ai"
                }
            else:
                raise ValueError("No valid JSON found in Claude response")
                
        except Exception as e:
            self.logger.error(f"Claude evaluation parsing failed: {e}")
            raise e
    
    def _enhanced_fallback_evaluation(self, question: Dict, response_text: str) -> Dict[str, Any]:
        """Enhanced fallback evaluation with better logic"""
        
        expected_keywords = question.get('expected_keywords', [])
        difficulty = question.get('difficulty', 'intermediate')
        skill_category = question.get('skill_category', 'general')
        
        # Enhanced keyword matching
        response_lower = response_text.lower()
        keywords_found = []
        
        if expected_keywords:
            for keyword in expected_keywords:
                if keyword.lower() in response_lower:
                    keywords_found.append(keyword)
        
        # Scoring logic based on difficulty
        word_count = len(response_text.split())
        
        # Base scoring
        base_score = 1.0  # Base for any response
        
        # Keyword scoring (adjusted by difficulty)
        keyword_multiplier = {"beginner": 0.6, "intermediate": 0.5, "advanced": 0.4}
        keyword_bonus = min(2.0, len(keywords_found) * keyword_multiplier.get(difficulty, 0.5))
        
        # Length scoring (adjusted by difficulty)
        length_targets = {"beginner": 30, "intermediate": 50, "advanced": 80}
        target_length = length_targets.get(difficulty, 50)
        length_bonus = min(1.5, word_count / target_length)
        
        # Complexity bonus for advanced responses
        complexity_indicators = ["because", "however", "therefore", "for example", "specifically", "additionally"]
        complexity_count = sum(1 for indicator in complexity_indicators if indicator in response_lower)
        complexity_bonus = min(0.5, complexity_count * 0.1)
        
        final_score = min(5.0, base_score + keyword_bonus + length_bonus + complexity_bonus)
        
        # Generate contextual feedback
        strengths = []
        improvements = []
        
        if len(keywords_found) >= 3:
            strengths.append("Used relevant Excel terminology")
        elif len(keywords_found) >= 1:
            strengths.append("Mentioned key concepts")
        else:
            improvements.append("Include more Excel-specific terms")
        
        if word_count >= target_length:
            strengths.append("Provided detailed explanation")
        elif word_count >= target_length * 0.6:
            strengths.append("Good explanation length")
        else:
            improvements.append("Provide more detailed explanation")
        
        if complexity_count >= 2:
            strengths.append("Used clear explanatory language")
        else:
            improvements.append("Add examples or more explanation")
        
        # Difficulty-specific feedback
        if difficulty == "advanced" and final_score < 3.0:
            improvements.append("Advanced questions require more sophisticated answers")
        elif difficulty == "beginner" and final_score >= 4.0:
            strengths.append("Excellent understanding of fundamentals")
        
        if not strengths:
            strengths = ["Response provided"]
        if not improvements:
            improvements = ["Great response!"]
        
        return {
            "score": round(final_score, 1),
            "confidence": 0.75,
            "reasoning": f"Enhanced evaluation: {len(keywords_found)} keywords found, {word_count} words, {difficulty} level question in {skill_category}",
            "strengths": strengths[:4],  # Limit to top 4
            "areas_for_improvement": improvements[:3],  # Limit to top 3
            "keywords_found": keywords_found,
            "mistakes_detected": [],
            "evaluation_method": "enhanced_fallback",
            "word_count": word_count,
            "keyword_coverage": f"{len(keywords_found)}/{len(expected_keywords)}" if expected_keywords else "N/A"
        }
    
    def _update_average_score(self, score: float):
        """Update running average score"""
        try:
            if self.stats["evaluations_performed"] == 1:
                self.stats["average_score"] = score
            else:
                alpha = 1.0 / self.stats["evaluations_performed"]
                self.stats["average_score"] = (1 - alpha) * self.stats["average_score"] + alpha * score
        except Exception as e:
            self.logger.warning(f"Stats update failed: {e}")
    
    def get_evaluation_stats(self) -> Dict[str, Any]:
        """Get evaluation statistics"""
        
        claude_percentage = 0
        fallback_percentage = 0
        
        if self.stats["evaluations_performed"] > 0:
            claude_percentage = (self.stats["claude_evaluations"] / self.stats["evaluations_performed"]) * 100
            fallback_percentage = (self.stats["fallback_evaluations"] / self.stats["evaluations_performed"]) * 100
        
        return {
            "evaluations_performed": self.stats["evaluations_performed"],
            "claude_evaluations": self.stats["claude_evaluations"],
            "fallback_evaluations": self.stats["fallback_evaluations"],
            "claude_usage_percentage": round(claude_percentage, 2),
            "fallback_usage_percentage": round(fallback_percentage, 2),
            "average_score": round(self.stats["average_score"], 2),
            "claude_available": self.available
        }

# =============================================================================
# COMPLETE INTERVIEW ORCHESTRATOR
# =============================================================================

# Import the complete orchestrator from the separate file
from interview_orchestrator import VoiceEnhancedInterviewOrchestrator

# =============================================================================
# SETTINGS
# =============================================================================

class Settings:
    """Complete settings configuration"""
    
    def __init__(self):
        load_dotenv()
        
        self.app_name = os.getenv('APP_NAME', 'Excel Interview System')
        self.app_version = os.getenv('APP_VERSION', '5.0.0-complete')
        self.debug = os.getenv('DEBUG', 'true').lower() == 'true'
        self.host = os.getenv('HOST', '0.0.0.0')
        self.port = int(os.getenv('PORT', 8000))
        
        # API Keys
        self.anthropic_api_key = (
            os.getenv('ANTHROPIC_API_KEY') or 
            os.getenv('anthropic_api_key') )
        
        self.murf_api_key = (
            os.getenv('MURF_API_KEY') or
            os.getenv('murf_api_key') or
       
        )
        
        self.default_voice_id = os.getenv('DEFAULT_VOICE_ID', 'en-US-sarah')
        
        # File limits
        self.max_file_size_mb = int(os.getenv('MAX_FILE_SIZE_MB', 50))
        self.max_audio_duration = int(os.getenv('MAX_AUDIO_DURATION_SECONDS', 300))
        
        # Create all necessary directories
        directories = ['voice_cache', 'uploads', 'temp_audio', 'audio_responses']
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"✅ Settings initialized - Voice: {bool(self.murf_api_key)}, Claude: {bool(self.anthropic_api_key)}")

settings = Settings()

# =============================================================================
# COMPLETE INITIALIZATION
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Complete application initialization with all services"""
    
    logger.info("🚀 Starting Complete Excel Interview System...")
    
    try:
        # Initialize all services
        logger.info("🔧 Initializing Murf client...")
        
        logger.info("🔧 Initializing voice service...")
        # Initialize FIXED voice system
        murf_client, voice_service = initialize_working_voice_system(settings.murf_api_key)
        # FIX: Use working voice ID from your account
        murf_client.default_voice_id = "en-US-cooper"
        print(f"🎙️ Forced voice ID to: {murf_client.default_voice_id}")
        
        logger.info("🔧 Initializing evaluation engine...")
        evaluation_engine = EvaluationEngine(settings.anthropic_api_key)
        
        logger.info("🔧 Initializing question bank...")
        question_bank = QuestionBank()
        
        logger.info("🔧 Initializing voice-enhanced orchestrator...")
        orchestrator = VoiceEnhancedInterviewOrchestrator(
            evaluation_engine=evaluation_engine, 
            question_bank=question_bank, 
            voice_service=voice_service
        )
        
        # Store all services in app state
        app.state.murf_client = murf_client
        app.state.voice_service = voice_service
        app.state.evaluation_engine = evaluation_engine
        app.state.question_bank = question_bank
        app.state.orchestrator = orchestrator
        app.state.voice_orchestrator = orchestrator  # Same instance, different alias
        
        # Test all services
        logger.info("🧪 Testing service health...")
        
        # Test voice service
        voice_health = await voice_service.health_check()
        logger.info(f"🎙️ Voice service: {'✅ Healthy' if voice_health.get('healthy') else '❌ Issues detected'}")
        
        # Test evaluation engine
        eval_stats = evaluation_engine.get_evaluation_stats()
        logger.info(f"🤖 Evaluation engine: {'✅ Claude available' if evaluation_engine.available else '⚠️ Fallback mode'}")
        
        # Test question bank
        qb_status = question_bank.get_status()
        logger.info(f"📚 Question bank: ✅ {qb_status['total_questions']} questions loaded")
        
        logger.info("✅ Complete system initialized successfully")
        
        # Log system capabilities
        capabilities = {
            "voice_synthesis": voice_health.get('healthy', False),
            "ai_evaluation": evaluation_engine.available,
            "question_bank": qb_status['total_questions'] > 0,
            "voice_interviews": voice_service.available,
            "text_interviews": True
        }
        
        logger.info(f"🎯 System capabilities: {capabilities}")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Initialization failed: {e}")
        # Create minimal fallback services
        app.state.orchestrator = VoiceEnhancedInterviewOrchestrator()
        app.state.voice_service = None
        app.state.evaluation_engine = EvaluationEngine()
        app.state.question_bank = QuestionBank()
        yield
    
    logger.info("🛑 Shutting down complete system...")

# =============================================================================
# COMPLETE FASTAPI APP
# =============================================================================

app = FastAPI(
    title=settings.app_name,
    description="Complete Production-Ready Excel Interview System with Full Voice Integration",
    version=settings.app_version,
    lifespan=lifespan
)

# Enhanced CORS for development and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for audio serving
try:
    voice_cache_dir = Path("voice_cache")
    voice_cache_dir.mkdir(exist_ok=True)
    app.mount("/audio", StaticFiles(directory=str(voice_cache_dir)), name="audio")
    logger.info("✅ Audio static files mounted at /audio")
except Exception as e:
    logger.warning(f"Failed to mount audio static files: {e}")

# =============================================================================
# COMPLETE REQUEST/RESPONSE MODELS
# =============================================================================

class StartInterviewRequest(BaseModel):
    candidate_name: Optional[str] = Field(None, max_length=100, description="Candidate's name")
    audio_mode: bool = Field(True, description="Enable voice features")
    skill_level: Optional[str] = Field("adaptive", description="Skill level preference")

class StartVoiceInterviewRequest(BaseModel):
    candidate_name: str = Field(..., max_length=100, description="Candidate's name")
    voice_id: str = Field("en-US-sarah", description="Preferred voice ID")

class SubmitResponseRequest(BaseModel):
    response_text: str = Field(..., min_length=1, max_length=10000, description="Text response")
    time_taken_seconds: int = Field(0, ge=0, le=3600, description="Time taken in seconds")
    confidence_level: Optional[int] = Field(None, ge=1, le=5, description="Self-assessed confidence")

class VoiceResponseRequest(BaseModel):
    response_text: Optional[str] = Field("", max_length=10000, description="Text response")
    time_taken_seconds: int = Field(0, ge=0, le=3600, description="Time taken in seconds")

# =============================================================================
# COMPLETE API ENDPOINTS
# =============================================================================

@app.get("/")
async def root():
    """Enhanced root endpoint with full system information"""
    
    try:
        # Get system status
        orchestrator = getattr(app.state, 'orchestrator', None)
        voice_service = getattr(app.state, 'voice_service', None)
        evaluation_engine = getattr(app.state, 'evaluation_engine', None)
        
        system_status = {
            "orchestrator_available": orchestrator is not None,
            "voice_service_available": voice_service and voice_service.available,
            "evaluation_engine_available": evaluation_engine and evaluation_engine.available,
            "question_bank_loaded": orchestrator and hasattr(orchestrator, 'question_bank')
        }
        
        return {
            "message": "Complete Excel Interview System with Full Voice Integration",
            "version": settings.app_version,
            "status": "operational",
            "timestamp": datetime.utcnow().isoformat(),
            "features": [
                "🎙️ Murf Voice Synthesis", 
                "🤖 Claude AI Assessment", 
                "📊 Performance Analysis",
                "🎯 Adaptive Questioning",
                "📋 Detailed Reporting",
                "🔊 Audio Feedback",
                "📱 Multi-Modal Interface"
            ],
            "endpoints": {
                "docs": "/docs",
                "health": "/health",
                "start_interview": "/api/interview/start",
                "start_voice_interview": "/api/interview/start-voice",
                "voice_synthesize": "/api/voice/synthesize",
                "available_voices": "/api/voice/voices"
            },
            "system_status": system_status
        }
    except Exception as e:
        return {
            "message": "Excel Interview System",
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/health")
async def comprehensive_health_check():
    """Comprehensive health check for all system components"""
    
    health_data = {
        "healthy": True,
        "status": "healthy",
        "version": settings.app_version,
        "timestamp": datetime.utcnow().isoformat(),
        "components": {},
        "system_stats": {},
        "issues": []
    }
    
    try:
        # Check orchestrator
        orchestrator = getattr(app.state, 'orchestrator', None)
        if orchestrator:
            health_data["components"]["orchestrator"] = {
                "available": True,
                "type": "VoiceEnhancedInterviewOrchestrator",
                "active_sessions": len(orchestrator.sessions),
                "system_stats": orchestrator.get_system_stats()
            }
        else:
            health_data["components"]["orchestrator"] = {"available": False}
            health_data["issues"].append("Orchestrator not initialized")
            health_data["healthy"] = False
        
        # Check voice service
        voice_service = getattr(app.state, 'voice_service', None)
        if voice_service:
            voice_health = await voice_service.health_check()
            health_data["components"]["voice_service"] = {
                "available": voice_service.available,
                "healthy": voice_health.get("healthy", False),
                "stats": voice_service.get_service_stats()
            }
            if not voice_health.get("healthy", False):
                health_data["issues"].append(f"Voice service issues: {voice_health.get('error', 'Unknown')}")
        else:
            health_data["components"]["voice_service"] = {"available": False}
            health_data["issues"].append("Voice service not initialized")
        
        # Check evaluation engine
        evaluation_engine = getattr(app.state, 'evaluation_engine', None)
        if evaluation_engine:
            health_data["components"]["evaluation_engine"] = {
                "available": True,
                "claude_available": evaluation_engine.available,
                "stats": evaluation_engine.get_evaluation_stats()
            }
        else:
            health_data["components"]["evaluation_engine"] = {"available": False}
            health_data["issues"].append("Evaluation engine not initialized")
        
        # Check question bank
        question_bank = getattr(app.state, 'question_bank', None)
        if question_bank:
            qb_status = question_bank.get_status()
            health_data["components"]["question_bank"] = {
                "available": True,
                "status": qb_status
            }
        else:
            health_data["components"]["question_bank"] = {"available": False}
            health_data["issues"].append("Question bank not initialized")
        
        # API Keys status (without exposing actual keys)
        health_data["api_keys_configured"] = {
            "anthropic": bool(settings.anthropic_api_key and settings.anthropic_api_key != "test_key"),
            "murf": bool(settings.murf_api_key and settings.murf_api_key != "test_key")
        }
        
        # Available features
        health_data["available_features"] = {
            "text_interviews": True,
            "voice_interviews": voice_service and voice_service.available,
            "ai_evaluation": evaluation_engine and evaluation_engine.available,
            "voice_synthesis": voice_service and voice_service.available,
            "file_uploads": True,
            "detailed_reporting": True
        }
        
        # Overall health determination
        critical_issues = [issue for issue in health_data["issues"] if "not initialized" in issue]
        if critical_issues:
            health_data["healthy"] = False
            health_data["status"] = "degraded"
        elif health_data["issues"]:
            health_data["status"] = "issues_detected"
        
        return health_data
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "healthy": False,
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# =============================================================================
# INTERVIEW ENDPOINTS (Complete Implementation)
# =============================================================================

@app.post("/api/interview/start")
async def start_interview(request: StartInterviewRequest):
    """Start standard interview with enhanced features"""
    
    try:
        orchestrator = getattr(app.state, 'orchestrator', None)
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Interview system not available")
        
        result = await orchestrator.start_interview(
            candidate_name=request.candidate_name,
            skill_level=request.skill_level
        )
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Interview start failed"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Interview start failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/interview/start-voice")
async def start_voice_interview(
    candidate_name: str = Form(...),
    voice_id: str = Form("en-US-sarah")
):
    """Start voice-enabled interview with full audio generation"""
    
    try:
        orchestrator = getattr(app.state, 'orchestrator', None)
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Interview system not available")
        
        # Check if it's a voice-enhanced orchestrator
        if hasattr(orchestrator, 'start_voice_interview'):
            result = await orchestrator.start_voice_interview(
                candidate_name=candidate_name,
                voice_id=voice_id
            )
        else:
            # Fallback to regular interview
            result = await orchestrator.start_interview(candidate_name)
            result["audio_mode"] = False
            result["note"] = "Voice features not available - using text mode"
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Voice interview start failed"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice interview start failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/interview/{session_id}/respond-text")
async def submit_text_response(session_id: str, request: SubmitResponseRequest):
    """Submit text response with enhanced processing"""
    
    try:
        orchestrator = getattr(app.state, 'orchestrator', None)
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Interview system not available")
        
        result = await orchestrator.submit_response(
            session_id=session_id,
            response_text=request.response_text,
            time_taken=request.time_taken_seconds
        )
        
        if result.get("success"):
            return result
        else:
            if "not found" in result.get("error", "").lower():
                raise HTTPException(status_code=404, detail="Session not found")
            else:
                raise HTTPException(status_code=500, detail=result.get("error"))
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text response submission failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/interview/{session_id}/respond-voice")
async def submit_voice_response(
    session_id: str,
    response_text: str = Form(""),
    audio_file: UploadFile = File(None),
    time_taken_seconds: int = Form(0)
):
    """Submit voice response with comprehensive audio handling"""
    
    try:
        orchestrator = getattr(app.state, 'orchestrator', None)
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Interview system not available")
        
        audio_file_path = None
        
        # Handle audio file if provided
        if audio_file:
            # Validate audio file
            if not audio_file.content_type or not audio_file.content_type.startswith('audio/'):
                raise HTTPException(status_code=400, detail="Invalid audio file type")
            
            # Check file size
            file_size = 0
            audio_content = await audio_file.read()
            file_size = len(audio_content)
            
            if file_size > settings.max_file_size_mb * 1024 * 1024:
                raise HTTPException(status_code=413, detail=f"Audio file too large (max {settings.max_file_size_mb}MB)")
            
            # Save audio file with proper naming
            audio_dir = Path("temp_audio")
            audio_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_extension = Path(audio_file.filename).suffix if audio_file.filename else ".wav"
            audio_file_path = audio_dir / f"{session_id}_{timestamp}_{uuid.uuid4().hex[:8]}{file_extension}"
            
            # Write audio file
            async with aiofiles.open(audio_file_path, 'wb') as f:
                await f.write(audio_content)
            
            logger.info(f"✅ Audio file saved: {audio_file_path}")
        
        # Submit response using voice method if available
        if hasattr(orchestrator, 'submit_voice_response'):
            result = await orchestrator.submit_voice_response(
                session_id=session_id,
                response_text=response_text if response_text.strip() else None,
                audio_file_path=str(audio_file_path) if audio_file_path else None,
                time_taken=time_taken_seconds
            )
        else:
            # Fallback to regular response submission
            result = await orchestrator.submit_response(
                session_id=session_id,
                response_text=response_text or "Audio response provided",
                time_taken=time_taken_seconds
            )
        
        # Clean up temporary audio file
        if audio_file_path and Path(audio_file_path).exists():
            try:
                await asyncio.sleep(1)  # Brief delay to ensure file isn't in use
                Path(audio_file_path).unlink()
                logger.info(f"✅ Temporary audio file cleaned up: {audio_file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up audio file: {e}")
        
        if result.get("success"):
            return result
        else:
            if "not found" in result.get("error", "").lower():
                raise HTTPException(status_code=404, detail="Session not found")
            else:
                raise HTTPException(status_code=500, detail=result.get("error"))
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice response submission failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/interview/{session_id}/status")
async def get_interview_status(session_id: str):
    """Get comprehensive interview status"""
    
    try:
        orchestrator = getattr(app.state, 'orchestrator', None)
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Interview system not available")
        
        # Get detailed status
        status_result = await orchestrator.get_session_status(session_id)
        
        if status_result.get("success"):
            # Add voice session details if available
            if hasattr(orchestrator, 'get_voice_session_details'):
                voice_details = await orchestrator.get_voice_session_details(session_id)
                if voice_details.get("success"):
                    status_result["voice_session"] = voice_details
            
            return status_result
        else:
            if "not found" in status_result.get("error", "").lower():
                raise HTTPException(status_code=404, detail="Session not found")
            else:
                raise HTTPException(status_code=500, detail=status_result.get("error"))
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/interview/{session_id}/report")
async def get_interview_report(session_id: str):
    """Generate comprehensive interview report"""
    
    try:
        orchestrator = getattr(app.state, 'orchestrator', None)
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Interview system not available")
        
        if session_id not in orchestrator.sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Generate text report
        text_report = await orchestrator.generate_final_report(session_id)
        
        # Get session data
        session_data = orchestrator.sessions[session_id]
        
        response_data = {
            "session_id": session_id,
            "report": text_report,
            "session_summary": {
                "candidate_name": session_data.get("candidate_name"),
                "status": session_data.get("status"),
                "final_score": session_data.get("final_score"),
                "questions_completed": len(session_data.get("questions_asked", [])),
                "duration_minutes": orchestrator._calculate_duration(session_data),
                "skills_covered": session_data.get("skills_covered", {}),
                "start_time": session_data.get("start_time").isoformat() if session_data.get("start_time") else None,
                "end_time": session_data.get("end_time").isoformat() if session_data.get("end_time") else None
            }
        }
        
        # Add voice analysis if available
        if hasattr(orchestrator, 'voice_sessions') and session_id in orchestrator.voice_sessions:
            voice_session = orchestrator.voice_sessions[session_id]
            response_data["voice_analysis"] = {
                "audio_files_count": len(voice_session.get("audio_files", [])),
                "audio_generation_count": len(voice_session.get("audio_generation_log", [])),
                "preferred_voice": voice_session.get("preferred_voice_id"),
                "voice_session_duration": orchestrator._calculate_voice_session_duration(voice_session)
            }
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sessions")
async def get_all_sessions():
    """Get all interview sessions summary"""
    
    try:
        orchestrator = getattr(app.state, 'orchestrator', None)
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Interview system not available")
        
        sessions_data = await orchestrator.get_all_sessions()
        
        if sessions_data.get("success"):
            return sessions_data
        else:
            raise HTTPException(status_code=500, detail=sessions_data.get("error"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sessions retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# VOICE ENDPOINTS (Complete Implementation)
# =============================================================================

@app.post("/api/voice/synthesize")
async def synthesize_speech(
    text: str = Form(...), 
    voice_id: Optional[str] = Form(None), 
    format: str = Form("mp3")
):
    """Complete speech synthesis endpoint with enhanced error handling"""
    
    try:
        voice_service = getattr(app.state, 'voice_service', None)
        if not voice_service:
            raise HTTPException(status_code=503, detail="Voice service not available")
        
        if not voice_service.available:
            raise HTTPException(status_code=503, detail="Voice service not configured")
        
        # Validate input
        if not text or len(text.strip()) == 0:
            raise HTTPException(status_code=400, detail="Text required")
        
        if len(text) > 5000:
            raise HTTPException(status_code=400, detail="Text too long (max 5000 characters)")
        
        # Synthesize speech
        result = await voice_service.text_to_speech(
            text=text.strip(), 
            voice_id=voice_id or settings.default_voice_id
        )
        
        if result["success"]:
            audio_path = result["audio_path"]
            if audio_path and Path(audio_path).exists():
                # Return audio file directly
                return FileResponse(
                    path=audio_path,
                    media_type=f"audio/{format}",
                    filename=f"speech.{format}",
                    headers={
                        "X-Voice-ID": result.get("voice_id"),
                        "X-Service": "murf",
                        "X-Text-Length": str(result.get("text_length", 0)),
                        "X-Audio-URL": result.get("audio_url", "")
                    }
                )
            else:
                raise HTTPException(status_code=500, detail="Audio file not found after generation")
        else:
            error_msg = result.get("error", "Speech synthesis failed")
            raise HTTPException(status_code=500, detail=error_msg)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Speech synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/voice/voices")
async def get_available_voices():
    """Get all available Murf voices with detailed information"""
    
    try:
        murf_client = getattr(app.state, 'murf_client', None)
        if not murf_client:
            raise HTTPException(status_code=503, detail="Voice service not available")
        
        voices = murf_client.get_default_voices()
        
        return {
            "success": True,
            "voices": voices,
            "total_voices": len(voices),
            "default_voice": settings.default_voice_id,
            "service": "murf",
            "voice_categories": {
                "us_english": [v for v in voices if v["language"] == "English (US)"],
                "uk_english": [v for v in voices if v["language"] == "English (UK)"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/voice/stats")
async def get_voice_statistics():
    """Get comprehensive voice service statistics"""
    
    try:
        voice_service = getattr(app.state, 'voice_service', None)
        orchestrator = getattr(app.state, 'orchestrator', None)
        
        if not voice_service:
            raise HTTPException(status_code=503, detail="Voice service not available")
        
        stats_data = {
            "voice_service_stats": voice_service.get_service_stats(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add orchestrator voice stats if available
        if orchestrator and hasattr(orchestrator, 'get_voice_stats'):
            stats_data["orchestrator_voice_stats"] = orchestrator.get_voice_stats()
        
        return stats_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/voice/test")
async def test_voice_service():
    """Test voice service with sample text"""
    
    try:
        voice_service = getattr(app.state, 'voice_service', None)
        if not voice_service:
            raise HTTPException(status_code=503, detail="Voice service not available")
        
        test_text = "This is a test of the Excel interview voice system. If you can hear this, the voice integration is working correctly."
        
        result = await voice_service.text_to_speech(test_text, "en-US-sarah")
        
        return {
            "test_successful": result.get("success", False),
            "result": result,
            "message": "Voice test completed",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Voice test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# SYSTEM ENDPOINTS (Complete Implementation)
# =============================================================================

@app.get("/api/system/stats")
async def get_system_statistics():
    """Get comprehensive system statistics"""
    
    try:
        stats_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "system_info": {
                "version": settings.app_version,
                "debug_mode": settings.debug,
                "uptime": "calculated_at_runtime"
            }
        }
        
        # Get orchestrator stats
        orchestrator = getattr(app.state, 'orchestrator', None)
        if orchestrator:
            stats_data["interview_stats"] = orchestrator.get_system_stats()
            
            if hasattr(orchestrator, 'get_voice_stats'):
                stats_data["voice_stats"] = orchestrator.get_voice_stats()
        
        # Get voice service stats
        voice_service = getattr(app.state, 'voice_service', None)
        if voice_service:
            stats_data["voice_service_stats"] = voice_service.get_service_stats()
        
        # Get evaluation engine stats
        evaluation_engine = getattr(app.state, 'evaluation_engine', None)
        if evaluation_engine:
            stats_data["evaluation_stats"] = evaluation_engine.get_evaluation_stats()
        
        # Get question bank stats
        question_bank = getattr(app.state, 'question_bank', None)
        if question_bank:
            stats_data["question_bank_stats"] = question_bank.get_status()
        
        return stats_data
        
    except Exception as e:
        logger.error(f"System stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/system/reset-question-bank")
async def reset_question_bank():
    """Reset question bank to start"""
    
    try:
        question_bank = getattr(app.state, 'question_bank', None)
        if not question_bank:
            raise HTTPException(status_code=503, detail="Question bank not available")
        
        question_bank.reset()
        
        return {
            "success": True,
            "message": "Question bank reset successfully",
            "status": question_bank.get_status(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Question bank reset failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# ERROR HANDLERS (Complete Implementation)
# =============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Comprehensive global exception handler"""
    
    logger.error(f"Global error on {request.method} {request.url}: {exc}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": str(uuid.uuid4()),
            "support_message": "Please check system logs or contact support"
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Enhanced HTTP exception handler"""
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat(),
            "request_path": str(request.url.path),
            "request_method": request.method
        }
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle validation errors"""
    
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation error",
            "message": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# =============================================================================
# STARTUP AND TESTING
# =============================================================================

async def run_startup_tests():
    """Run comprehensive startup tests"""
    
    logger.info("🧪 Running startup tests...")
    
    
        # Test orchestrator
    orchestrator = getattr(app.state, 'orchestrator', None)
    if orchestrator:
            logger.info("✅ Orchestrator available")
            
            # Test basic interview start
            test_result = await orchestrator.start_interview("Startup Test")
            if test_result.get("success"):
                logger.info("✅ Basic interview start test passed")