# main_minimal.py - Minimal Working Version
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import logging
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple FastAPI app
app = FastAPI(
    title="Excel Interview System",
    description="Minimal working version",
    version="4.0.0-minimal"
)

# Simple CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Excel Interview System API",
        "status": "operational",
        "version": "4.0.0-minimal"
    }

@app.get("/health")
async def health_check():
    return {
        "healthy": True,
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "available_features": {
            "text_interviews": True,
            "voice_interviews": False,
            "question_bank": False,
            "audio_processing": False
        }
    }

@app.post("/api/interview/start")
async def start_interview():
    session_id = f"demo_{uuid.uuid4().hex[:8]}"
    return {
        "session_id": session_id,
        "first_question": {
            "text": "Explain the difference between VLOOKUP and INDEX-MATCH functions in Excel.",
            "type": "conceptual",
            "skill_category": "lookup_functions",
            "difficulty": "intermediate"
        },
        "welcome_message": "Interview started successfully!",
        "status": "started"
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting minimal Excel Interview System...")
    uvicorn.run("main_minimal:app", host="0.0.0.0", port=8000, reload=True)
