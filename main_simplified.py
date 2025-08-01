# main_fixed.py - Working Excel Interview System
"""
Fixed version with proper error handling and simplified architecture
"""

import asyncio
import logging
import uuid
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# MODELS
# =============================================================================

class InterviewQuestion(BaseModel):
    id: str
    text: str
    type: str = "free_text"
    difficulty: str = "medium"

class InterviewResponse(BaseModel):
    question_id: str
    response_text: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SessionData(BaseModel):
    session_id: str
    candidate_name: str
    status: str = "active"
    current_question_index: int = 0
    responses: List[InterviewResponse] = Field(default_factory=list)
    start_time: datetime = Field(default_factory=datetime.utcnow)
    scores: List[float] = Field(default_factory=list)

# =============================================================================
# VOICE SERVICE (Mock Implementation)
# =============================================================================

class MockVoiceService:
    """Mock voice service for testing without external dependencies"""
    
    def __init__(self):
        self.available = True
        logger.info("🎙️ Mock voice service initialized")
    
    async def text_to_speech(self, text: str, voice_id: str = "en-US-cooper") -> Dict[str, Any]:
        """Mock TTS that returns success without actual audio generation"""
        
        # Simulate processing time
        await asyncio.sleep(0.1)
        
        # Create mock audio file path
        audio_filename = f"mock_audio_{uuid.uuid4().hex[:8]}.mp3"
        
        return {
            "success": True,
            "audio_url": f"/audio/{audio_filename}",
            "voice_id": voice_id,
            "text_length": len(text),
            "message": "Mock audio generated successfully"
        }

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
# APPLICATION SETUP
# =============================================================================

app = FastAPI(
    title="Excel Interview System",
    description="Interactive Excel skills assessment platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories
Path("voice_cache").mkdir(exist_ok=True)
Path("uploads").mkdir(exist_ok=True)

# Mount static files (with error handling)
try:
    app.mount("/audio", StaticFiles(directory="voice_cache"), name="audio")
    logger.info("✅ Audio files mounted successfully")
except Exception as e:
    logger.warning(f"⚠️ Could not mount audio files: {e}")

# Initialize services
voice_service = MockVoiceService()

# In-memory session storage (replace with database in production)
active_sessions: Dict[str, SessionData] = {}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def evaluate_response(question: Dict[str, Any], response_text: str) -> Dict[str, Any]:
    """Simple response evaluation logic"""
    
    if not response_text or len(response_text.strip()) < 10:
        return {
            "score": 1.0,
            "reasoning": "Response too short or empty",
            "feedback": "Please provide a more detailed answer."
        }
    
    # Basic scoring based on length and keywords
    word_count = len(response_text.split())
    
    # Look for relevant keywords based on question
    keywords = {
        "excel_001": ["vlookup", "index", "match", "lookup", "range", "exact"],
        "excel_002": ["pivot", "table", "insert", "data", "field", "summarize"],
        "excel_003": ["error", "div", "na", "ref", "formula", "reference"],
        "excel_004": ["conditional", "format", "highlight", "criteria", "rule"],
        "excel_005": ["array", "formula", "ctrl", "shift", "enter", "range"]
    }
    
    question_keywords = keywords.get(question["id"], [])
    keyword_matches = sum(1 for word in response_text.lower().split() 
                         if any(keyword in word for keyword in question_keywords))
    
    # Calculate score (1-5 scale)
    base_score = min(3.0, word_count * 0.05)  # Length component
    keyword_bonus = min(2.0, keyword_matches * 0.5)  # Keyword component
    final_score = min(5.0, base_score + keyword_bonus)
    
    # Generate feedback
    if final_score >= 4.0:
        feedback = "Excellent response with good technical details!"
    elif final_score >= 3.0:
        feedback = "Good response, could include more specific examples."
    elif final_score >= 2.0:
        feedback = "Adequate response, but lacks technical depth."
    else:
        feedback = "Response needs more detail and technical accuracy."
    
    return {
        "score": round(final_score, 1),
        "reasoning": f"Score based on length ({word_count} words) and keyword relevance ({keyword_matches} matches)",
        "feedback": feedback,
        "word_count": word_count,
        "keyword_matches": keyword_matches
    }

def get_next_question(current_index: int) -> Optional[Dict[str, Any]]:
    """Get the next question in sequence"""
    next_index = current_index + 1
    if next_index < len(EXCEL_QUESTIONS):
        return EXCEL_QUESTIONS[next_index]
    return None

# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint with system status"""
    return {
        "message": "Excel Interview System API",
        "status": "running",
        "version": "1.0.0",
        "voice_available": voice_service.available,
        "total_questions": len(EXCEL_QUESTIONS),
        "active_sessions": len(active_sessions),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "voice_service": voice_service.available,
        "questions_loaded": len(EXCEL_QUESTIONS),
        "sessions_active": len(active_sessions),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/questions")
async def get_questions():
    """Get all available questions"""
    return {
        "questions": EXCEL_QUESTIONS,
        "total": len(EXCEL_QUESTIONS)
    }

@app.post("/api/interview/start")
async def start_interview(request: Request):
    """Start a new interview session"""
    
    try:
        # Parse request body
        body = await request.json()
        candidate_name = body.get("candidate_name", "Anonymous")
        
    except Exception:
        # Fallback if no JSON body
        candidate_name = "Anonymous"
    
    # Generate session ID
    session_id = f"session_{uuid.uuid4().hex[:12]}"
    
    # Create session data
    session_data = SessionData(
        session_id=session_id,
        candidate_name=candidate_name,
        status="active",
        current_question_index=0
    )
    
    # Store session
    active_sessions[session_id] = session_data
    
    # Get first question
    first_question = EXCEL_QUESTIONS[0]
    
    logger.info(f"📝 Started interview for {candidate_name} (Session: {session_id})")
    
    return {
        "success": True,
        "session_id": session_id,
        "candidate_name": candidate_name,
        "first_question": first_question,
        "total_questions": len(EXCEL_QUESTIONS),
        "message": "Interview started successfully"
    }

@app.post("/api/interview/{session_id}/respond")
async def submit_response(session_id: str, request: Request):
    """Submit response to current question"""
    
    # Check if session exists
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = active_sessions[session_id]
    
    if session.status != "active":
        raise HTTPException(status_code=400, detail="Interview session is not active")
    
    try:
        # Parse request body
        body = await request.json()
        response_text = body.get("response_text", "").strip()
        
        if not response_text:
            raise HTTPException(status_code=400, detail="Response text is required")
        
        # Get current question
        current_question = EXCEL_QUESTIONS[session.current_question_index]
        
        # Evaluate response
        evaluation = evaluate_response(current_question, response_text)
        
        # Store response
        interview_response = InterviewResponse(
            question_id=current_question["id"],
            response_text=response_text
        )
        session.responses.append(interview_response)
        session.scores.append(evaluation["score"])
        
        # Check if interview is complete
        next_question = get_next_question(session.current_question_index)
        
        if next_question:
            # Move to next question
            session.current_question_index += 1
            interview_complete = False
            status = "in_progress"
        else:
            # Interview complete
            session.status = "completed"
            interview_complete = True
            status = "completed"
            
            # Calculate final score
            avg_score = sum(session.scores) / len(session.scores) if session.scores else 0
            logger.info(f"📊 Interview completed for {session.candidate_name}. Average score: {avg_score:.1f}")
        
        response_data = {
            "success": True,
            "evaluation": evaluation,
            "next_question": next_question,
            "status": status,
            "interview_complete": interview_complete,
            "progress": {
                "current": session.current_question_index + (0 if next_question else 1),
                "total": len(EXCEL_QUESTIONS)
            }
        }
        
        if interview_complete:
            response_data["final_results"] = {
                "average_score": round(sum(session.scores) / len(session.scores), 1),
                "total_responses": len(session.responses),
                "session_duration": str(datetime.utcnow() - session.start_time)
            }
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error processing response: {e}")
        raise HTTPException(status_code=500, detail="Error processing response")

@app.get("/api/interview/{session_id}/status")
async def get_interview_status(session_id: str):
    """Get current interview status"""
    
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = active_sessions[session_id]
    
    return {
        "session_id": session_id,
        "candidate_name": session.candidate_name,
        "status": session.status,
        "current_question_index": session.current_question_index,
        "total_questions": len(EXCEL_QUESTIONS),
        "responses_submitted": len(session.responses),
        "average_score": round(sum(session.scores) / len(session.scores), 1) if session.scores else 0,
        "start_time": session.start_time.isoformat(),
        "progress_percentage": round((len(session.responses) / len(EXCEL_QUESTIONS)) * 100, 1)
    }

@app.post("/api/voice/synthesize")
async def synthesize_speech(request: Request):
    """Generate speech from text"""
    
    if not voice_service or not voice_service.available:
        raise HTTPException(status_code=503, detail="Voice service not available")
    
    try:
        body = await request.json()
        text = body.get("text", "")
        voice_id = body.get("voice_id", "en-US-cooper")
        
        if not text:
            raise HTTPException(status_code=400, detail="Text is required")
        
        if len(text) > 1000:
            text = text[:1000]  # Limit text length
        
        result = await voice_service.text_to_speech(text, voice_id)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Voice synthesis error: {e}")
        raise HTTPException(status_code=500, detail="Voice synthesis failed")

@app.delete("/api/interview/{session_id}")
async def end_interview(session_id: str):
    """End interview session"""
    
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = active_sessions[session_id]
    session.status = "ended"
    
    # Calculate final results
    final_results = {
        "session_id": session_id,
        "candidate_name": session.candidate_name,
        "total_questions": len(EXCEL_QUESTIONS),
        "questions_answered": len(session.responses),
        "average_score": round(sum(session.scores) / len(session.scores), 1) if session.scores else 0,
        "session_duration": str(datetime.utcnow() - session.start_time),
        "completion_rate": round((len(session.responses) / len(EXCEL_QUESTIONS)) * 100, 1)
    }
    
    # Remove from active sessions after a delay (cleanup)
    asyncio.create_task(cleanup_session(session_id))
    
    logger.info(f"🏁 Interview ended for {session.candidate_name}")
    
    return {
        "success": True,
        "message": "Interview ended successfully",
        "final_results": final_results
    }

async def cleanup_session(session_id: str):
    """Clean up session after delay"""
    await asyncio.sleep(300)  # Keep for 5 minutes
    if session_id in active_sessions:
        del active_sessions[session_id]
        logger.info(f"🧹 Cleaned up session {session_id}")

@app.get("/api/sessions")
async def list_sessions():
    """List all active sessions (for debugging)"""
    return {
        "active_sessions": len(active_sessions),
        "sessions": [
            {
                "session_id": session.session_id,
                "candidate_name": session.candidate_name,
                "status": session.status,
                "progress": f"{len(session.responses)}/{len(EXCEL_QUESTIONS)}"
            }
            for session in active_sessions.values()
        ]
    }

# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={"detail": "Endpoint not found", "path": str(request.url.path)}
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    logger.error(f"Internal error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# =============================================================================
# STARTUP AND MAIN
# =============================================================================

def main():
    """Main function to run the application"""
    
    print("🚀 Starting Excel Interview System")
    print("=" * 50)
    print(f"✅ Questions loaded: {len(EXCEL_QUESTIONS)}")
    print(f"✅ Voice service available: {voice_service.available}")
    print(f"✅ Cache directory: voice_cache/")
    print(f"✅ Upload directory: uploads/")
    print("=" * 50)
    
    # Import here to avoid issues
    import uvicorn
    
    try:
        uvicorn.run(
            app,  # Pass app directly instead of module string
            host="0.0.0.0",
            port=8000,
            reload=False,  # Disable reload for stability
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n👋 Shutting down gracefully...")
    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()