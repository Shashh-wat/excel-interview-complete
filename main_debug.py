# main_debug.py - Excel Interview System with Enhanced Debugging
"""
Debug version with comprehensive error tracking and diagnostics
"""

import asyncio
import logging
import uuid
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Check Python version
print(f"🐍 Python version: {sys.version}")

try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from fastapi.staticfiles import StaticFiles
    from pydantic import BaseModel, Field
    print("✅ FastAPI imports successful")
except ImportError as e:
    print(f"❌ FastAPI import failed: {e}")
    print("Install with: pip install fastapi uvicorn")
    sys.exit(1)

# Enhanced logging setup
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('interview_debug.log')
    ]
)
logger = logging.getLogger(__name__)

# =============================================================================
# SYSTEM DIAGNOSTICS
# =============================================================================

class SystemDiagnostics:
    """Comprehensive system health checker"""
    
    def __init__(self):
        self.checks = {}
        self.errors = []
        self.warnings = []
    
    def check_directories(self):
        """Check required directories"""
        try:
            dirs = ["voice_cache", "uploads", "logs"]
            for dir_name in dirs:
                path = Path(dir_name)
                if not path.exists():
                    path.mkdir(exist_ok=True)
                    logger.info(f"📁 Created directory: {dir_name}")
                else:
                    logger.info(f"📁 Directory exists: {dir_name}")
                
                # Test write permissions
                test_file = path / "test_write.tmp"
                try:
                    test_file.write_text("test")
                    test_file.unlink()
                    self.checks[f"dir_{dir_name}"] = True
                except Exception as e:
                    self.errors.append(f"Cannot write to {dir_name}: {e}")
                    self.checks[f"dir_{dir_name}"] = False
        except Exception as e:
            self.errors.append(f"Directory check failed: {e}")
    
    def check_dependencies(self):
        """Check all required dependencies"""
        required_packages = [
            "fastapi", "uvicorn", "pydantic", "aiohttp", "aiofiles"
        ]
        
        for package in required_packages:
            try:
                __import__(package)
                self.checks[f"package_{package}"] = True
                logger.info(f"📦 Package available: {package}")
            except ImportError:
                self.checks[f"package_{package}"] = False
                self.errors.append(f"Missing package: {package}")
    
    def check_environment(self):
        """Check environment variables and system settings"""
        try:
            # Check environment variables
            env_vars = ["MURF_API_KEY", "ANTHROPIC_API_KEY"]
            for var in env_vars:
                value = os.getenv(var)
                if value:
                    self.checks[f"env_{var}"] = True
                    logger.info(f"🔑 Environment variable set: {var}")
                else:
                    self.checks[f"env_{var}"] = False
                    self.warnings.append(f"Environment variable not set: {var}")
            
            # Check system resources
            self.checks["python_version"] = sys.version_info >= (3, 7)
            if not self.checks["python_version"]:
                self.errors.append(f"Python version too old: {sys.version}")
            
        except Exception as e:
            self.errors.append(f"Environment check failed: {e}")
    
    def run_all_checks(self):
        """Run comprehensive system diagnostics"""
        logger.info("🔍 Starting system diagnostics...")
        
        try:
            self.check_directories()
            self.check_dependencies() 
            self.check_environment()
            
            # Summary
            total_checks = len(self.checks)
            passed_checks = sum(1 for v in self.checks.values() if v)
            
            logger.info(f"📊 Diagnostics complete: {passed_checks}/{total_checks} checks passed")
            
            if self.errors:
                logger.error("❌ Critical errors found:")
                for error in self.errors:
                    logger.error(f"  - {error}")
            
            if self.warnings:
                logger.warning("⚠️ Warnings:")
                for warning in self.warnings:
                    logger.warning(f"  - {warning}")
            
            return {
                "status": "healthy" if not self.errors else "unhealthy",
                "checks": self.checks,
                "errors": self.errors,
                "warnings": self.warnings,
                "summary": f"{passed_checks}/{total_checks} checks passed"
            }
            
        except Exception as e:
            logger.error(f"❌ Diagnostics failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "traceback": traceback.format_exc()
            }

# =============================================================================
# MODELS
# =============================================================================

class InterviewQuestion(BaseModel):
    id: str
    text: str
    type: str = "free_text"
    difficulty: str = "medium"

class InterviewSession(BaseModel):
    session_id: str
    candidate_name: str
    status: str = "active"
    current_question_index: int = 0
    responses: List[str] = Field(default_factory=list)
    scores: List[float] = Field(default_factory=list)
    start_time: datetime = Field(default_factory=datetime.utcnow)
    errors: List[str] = Field(default_factory=list)

# =============================================================================
# QUESTION BANK
# =============================================================================

EXCEL_QUESTIONS = [
    {
        "id": "excel_001",
        "text": "Explain the difference between VLOOKUP and INDEX-MATCH functions. When would you use each?",
        "type": "free_text",
        "difficulty": "medium"
    },
    {
        "id": "excel_002", 
        "text": "How do you create a pivot table? Walk me through the process step by step.",
        "type": "free_text",
        "difficulty": "easy"
    },
    {
        "id": "excel_003",
        "text": "What are the most common Excel errors (#DIV/0!, #N/A, #REF!) and how do you fix them?",
        "type": "free_text",
        "difficulty": "medium"
    },
    {
        "id": "excel_004",
        "text": "Describe how you would use conditional formatting to highlight cells based on specific criteria.",
        "type": "free_text", 
        "difficulty": "easy"
    },
    {
        "id": "excel_005",
        "text": "Explain array formulas in Excel. Give an example of when you'd use one.",
        "type": "free_text",
        "difficulty": "hard"
    }
]

# =============================================================================
# MOCK VOICE SERVICE
# =============================================================================

class DebugVoiceService:
    """Voice service with detailed debugging"""
    
    def __init__(self):
        self.available = True
        self.calls_made = 0
        self.errors = []
        logger.info("🎙️ Debug voice service initialized")
    
    async def text_to_speech(self, text: str, voice_id: str = "en-US-cooper") -> Dict[str, Any]:
        """Mock TTS with detailed logging"""
        
        try:
            self.calls_made += 1
            logger.info(f"🔊 TTS Call #{self.calls_made}: {len(text)} chars, voice: {voice_id}")
            
            # Simulate processing
            await asyncio.sleep(0.05)
            
            # Generate mock response
            audio_id = f"audio_{uuid.uuid4().hex[:8]}"
            
            result = {
                "success": True,
                "audio_url": f"/audio/{audio_id}.mp3",
                "voice_id": voice_id,
                "text_length": len(text),
                "call_number": self.calls_made,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"✅ TTS successful: {audio_id}")
            return result
            
        except Exception as e:
            error_msg = f"TTS Error: {e}"
            self.errors.append(error_msg)
            logger.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "call_number": self.calls_made
            }

# =============================================================================
# APPLICATION SETUP
# =============================================================================

# Run diagnostics first
diagnostics = SystemDiagnostics()
diagnostic_results = diagnostics.run_all_checks()

if diagnostic_results["status"] == "error":
    print("❌ Critical system error detected!")
    print(diagnostic_results.get("error", "Unknown error"))
    sys.exit(1)

# Create FastAPI app
try:
    app = FastAPI(
        title="Excel Interview System - Debug",
        description="Debug version with comprehensive error tracking",
        version="1.0.0-debug",
        debug=True
    )
    logger.info("✅ FastAPI app created")
except Exception as e:
    logger.error(f"❌ Failed to create FastAPI app: {e}")
    sys.exit(1)

# Add CORS
try:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info("✅ CORS middleware added")
except Exception as e:
    logger.error(f"❌ CORS setup failed: {e}")

# Mount static files with error handling
try:
    if Path("voice_cache").exists():
        app.mount("/audio", StaticFiles(directory="voice_cache"), name="audio")
        logger.info("✅ Static files mounted")
    else:
        logger.warning("⚠️ voice_cache directory not found")
except Exception as e:
    logger.warning(f"⚠️ Static files mount failed: {e}")

# Initialize services
try:
    voice_service = DebugVoiceService()
    sessions: Dict[str, InterviewSession] = {}
    logger.info("✅ Services initialized")
except Exception as e:
    logger.error(f"❌ Service initialization failed: {e}")
    voice_service = None

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def safe_evaluate_response(question: Dict[str, Any], response_text: str) -> Dict[str, Any]:
    """Safe response evaluation with error handling"""
    
    try:
        if not response_text or len(response_text.strip()) < 5:
            return {
                "score": 1.0,
                "reasoning": "Response too short",
                "feedback": "Please provide a more detailed answer.",
                "word_count": 0
            }
        
        words = response_text.split()
        word_count = len(words)
        
        # Simple scoring logic
        if word_count < 10:
            score = 1.5
            feedback = "Response is too brief. Add more detail."
        elif word_count < 30:
            score = 2.5
            feedback = "Good start, but could use more explanation."
        elif word_count < 60:
            score = 3.5
            feedback = "Well-detailed response!"
        else:
            score = 4.5
            feedback = "Excellent comprehensive response!"
        
        return {
            "score": score,
            "reasoning": f"Based on {word_count} words and content quality",
            "feedback": feedback,
            "word_count": word_count
        }
        
    except Exception as e:
        logger.error(f"❌ Evaluation error: {e}")
        return {
            "score": 0.0,
            "reasoning": f"Evaluation failed: {e}",
            "feedback": "Error processing response",
            "error": str(e)
        }

# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint with comprehensive status"""
    return {
        "message": "Excel Interview System - Debug Version",
        "status": "running",
        "diagnostics": diagnostic_results,
        "voice_service": {
            "available": voice_service.available if voice_service else False,
            "calls_made": voice_service.calls_made if voice_service else 0,
            "errors": voice_service.errors if voice_service else []
        },
        "data": {
            "questions_loaded": len(EXCEL_QUESTIONS),
            "active_sessions": len(sessions)
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    
    health_status = {
        "status": "healthy",
        "checks": {
            "app_running": True,
            "voice_service": voice_service.available if voice_service else False,
            "questions_loaded": len(EXCEL_QUESTIONS) > 0,
            "directories": all([
                Path("voice_cache").exists(),
                Path("uploads").exists()
            ])
        },
        "errors": [],
        "warnings": [],
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Add any accumulated errors
    if voice_service and voice_service.errors:
        health_status["warnings"].extend(voice_service.errors)
    
    # Overall health determination
    critical_checks = ["app_running", "questions_loaded"]
    if not all(health_status["checks"][check] for check in critical_checks):
        health_status["status"] = "unhealthy"
    
    return health_status

@app.get("/debug")
async def debug_info():
    """Comprehensive debug information"""
    
    return {
        "system": {
            "python_version": sys.version,
            "platform": sys.platform,
            "cwd": str(Path.cwd()),
            "script_path": __file__ if '__file__' in globals() else "Unknown"
        },
        "diagnostics": diagnostic_results,
        "services": {
            "voice_service": {
                "available": voice_service.available if voice_service else False,
                "calls_made": voice_service.calls_made if voice_service else 0,
                "errors": voice_service.errors if voice_service else []
            }
        },
        "data": {
            "questions": len(EXCEL_QUESTIONS),
            "sessions": len(sessions),
            "session_ids": list(sessions.keys())
        },
        "directories": {
            name: {
                "exists": Path(name).exists(),
                "is_dir": Path(name).is_dir() if Path(name).exists() else False,
                "writable": os.access(name, os.W_OK) if Path(name).exists() else False
            }
            for name in ["voice_cache", "uploads", "logs"]
        }
    }

@app.post("/api/interview/start")
async def start_interview(request: Request):
    """Start interview with enhanced error handling"""
    
    try:
        # Parse request safely
        try:
            body = await request.json()
            candidate_name = body.get("candidate_name", "Test Candidate")
        except Exception as e:
            logger.warning(f"⚠️ JSON parse failed, using defaults: {e}")
            candidate_name = "Test Candidate"
        
        # Generate session
        session_id = f"session_{uuid.uuid4().hex[:10]}"
        
        # Create session
        session = InterviewSession(
            session_id=session_id,
            candidate_name=candidate_name,
            status="active"
        )
        
        sessions[session_id] = session
        
        logger.info(f"📝 Interview started: {candidate_name} ({session_id})")
        
        # Get first question
        first_question = EXCEL_QUESTIONS[0]
        
        return {
            "success": True,
            "session_id": session_id,
            "candidate_name": candidate_name,
            "first_question": first_question,
            "total_questions": len(EXCEL_QUESTIONS),
            "debug_info": {
                "session_created": True,
                "questions_available": len(EXCEL_QUESTIONS),
                "voice_available": voice_service.available if voice_service else False
            }
        }
        
    except Exception as e:
        error_msg = f"Failed to start interview: {e}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": error_msg,
                "type": type(e).__name__,
                "traceback": traceback.format_exc()
            }
        )

@app.post("/api/interview/{session_id}/respond")
async def submit_response(session_id: str, request: Request):
    """Submit response with detailed error tracking"""
    
    try:
        # Validate session
        if session_id not in sessions:
            logger.error(f"❌ Session not found: {session_id}")
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        session = sessions[session_id]
        
        if session.status != "active":
            raise HTTPException(status_code=400, detail=f"Session status is {session.status}, not active")
        
        # Parse request
        try:
            body = await request.json()
            response_text = body.get("response_text", "").strip()
        except Exception as e:
            logger.error(f"❌ Request parsing failed: {e}")
            raise HTTPException(status_code=400, detail="Invalid request format")
        
        if not response_text:
            raise HTTPException(status_code=400, detail="Response text is required")
        
        # Get current question
        if session.current_question_index >= len(EXCEL_QUESTIONS):
            raise HTTPException(status_code=400, detail="No more questions available")
        
        current_question = EXCEL_QUESTIONS[session.current_question_index]
        
        # Evaluate response
        evaluation = safe_evaluate_response(current_question, response_text)
        
        # Store response and score
        session.responses.append(response_text)
        session.scores.append(evaluation["score"])
        
        # Determine next question
        session.current_question_index += 1
        
        if session.current_question_index < len(EXCEL_QUESTIONS):
            next_question = EXCEL_QUESTIONS[session.current_question_index]
            interview_complete = False
        else:
            next_question = None
            interview_complete = True
            session.status = "completed"
        
        logger.info(f"📊 Response evaluated: {evaluation['score']}/5.0 for {session.candidate_name}")
        
        response_data = {
            "success": True,
            "evaluation": evaluation,
            "next_question": next_question,
            "interview_complete": interview_complete,
            "progress": {
                "current": session.current_question_index,
                "total": len(EXCEL_QUESTIONS),
                "percentage": round((session.current_question_index / len(EXCEL_QUESTIONS)) * 100, 1)
            },
            "debug_info": {
                "session_status": session.status,
                "responses_count": len(session.responses),
                "average_score": round(sum(session.scores) / len(session.scores), 2) if session.scores else 0
            }
        }
        
        if interview_complete:
            response_data["final_results"] = {
                "total_questions": len(EXCEL_QUESTIONS),
                "average_score": round(sum(session.scores) / len(session.scores), 2),
                "session_duration": str(datetime.utcnow() - session.start_time),
                "completion_rate": 100.0
            }
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Response processing failed: {e}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        
        # Log to session if possible
        if session_id in sessions:
            sessions[session_id].errors.append(error_msg)
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": error_msg,
                "session_id": session_id,
                "traceback": traceback.format_exc()
            }
        )

@app.post("/api/voice/test")
async def test_voice():
    """Test voice service with detailed debugging"""
    
    if not voice_service:
        raise HTTPException(status_code=503, detail="Voice service not initialized")
    
    try:
        test_text = "This is a test of the debug voice system. Can you hear this clearly?"
        
        logger.info(f"🔊 Testing voice with: '{test_text[:50]}...'")
        
        result = await voice_service.text_to_speech(test_text)
        
        return {
            "test_successful": result.get("success", False),
            "result": result,
            "service_stats": {
                "total_calls": voice_service.calls_made,
                "total_errors": len(voice_service.errors)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        error_msg = f"Voice test failed: {e}"
        logger.error(error_msg)
        
        raise HTTPException(
            status_code=500, 
            detail={
                "error": error_msg,
                "traceback": traceback.format_exc()
            }
        )

@app.get("/api/sessions")
async def list_sessions():
    """List all sessions with detailed info"""
    
    return {
        "total_sessions": len(sessions),
        "sessions": [
            {
                "session_id": session.session_id,
                "candidate_name": session.candidate_name,
                "status": session.status,
                "progress": f"{len(session.responses)}/{len(EXCEL_QUESTIONS)}",
                "average_score": round(sum(session.scores) / len(session.scores), 2) if session.scores else 0,
                "duration": str(datetime.utcnow() - session.start_time),
                "errors": len(session.errors)
            }
            for session in sessions.values()
        ]
    }

# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with detailed logging"""
    
    error_id = uuid.uuid4().hex[:8]
    error_msg = f"Unhandled error {error_id}: {exc}"
    
    logger.error(error_msg)
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=500,
        content={
            "error_id": error_id,
            "error": str(exc),
            "type": type(exc).__name__,
            "path": str(request.url.path),
            "method": request.method,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# =============================================================================
# STARTUP FUNCTION
# =============================================================================

def main():
    """Main function with comprehensive error handling"""
    
    print("\n" + "="*60)
    print("🚀 EXCEL INTERVIEW SYSTEM - DEBUG VERSION")
    print("="*60)
    
    # Print diagnostics
    print(f"📊 System Status: {diagnostic_results['status'].upper()}")
    print(f"✅ Questions loaded: {len(EXCEL_QUESTIONS)}")
    print(f"🎙️ Voice service: {voice_service.available if voice_service else False}")
    
    if diagnostic_results["errors"]:
        print("❌ Errors found:")
        for error in diagnostic_results["errors"]:
            print(f"   - {error}")
    
    if diagnostic_results["warnings"]:
        print("⚠️ Warnings:")
        for warning in diagnostic_results["warnings"]:
            print(f"   - {warning}")
    
    print("="*60)
    print("🌐 Starting server...")
    print("📍 URL: http://localhost:8000")
    print("🔍 Debug info: http://localhost:8000/debug")
    print("❤️ Health check: http://localhost:8000/health")
    print("="*60)
    
    try:
        import uvicorn
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="debug",
            access_log=True,
            reload=False
        )
        
    except KeyboardInterrupt:
        print("\n👋 Graceful shutdown...")
    except Exception as e:
        print(f"\n❌ Server failed to start: {e}")
        print(f"Traceback:\n{traceback.format_exc()}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)