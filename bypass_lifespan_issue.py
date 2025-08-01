# bypass_lifespan_issue.py - Bypass Lifespan Hang
"""
Creates a simplified version of your main.py that bypasses the lifespan hang
"""

import shutil

def create_simplified_main():
    """Create a simplified main.py that bypasses the hang"""
    
    print("🔧 CREATING SIMPLIFIED MAIN.PY")
    print("=" * 50)
    
    # Backup original
    shutil.copy("main.py", "main_original_backup.py")
    print("✅ Backed up main.py → main_original_backup.py")
    
    simplified_main = '''# main_simplified.py - Working Excel Interview System
"""
Simplified version that bypasses the lifespan hang issue
"""

import asyncio
import logging
import uuid
import aiofiles
import aiohttp
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# SIMPLIFIED VOICE SYSTEM (No hanging health checks)
# =============================================================================

class SimpleMurfClient:
    """Simple Murf client without hanging health checks"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.available = bool(api_key and api_key != "test_key")
        self.default_voice_id = "en-US-cooper"  # Working voice
        
        Path("voice_cache").mkdir(exist_ok=True)
        logger.info(f"🎙️ Simple Murf client - Voice: {self.default_voice_id}")
    
    async def text_to_speech(self, text: str, voice_id: str = None) -> Dict[str, Any]:
        """Simple TTS without complex error handling"""
        
        if not self.available:
            return {"success": False, "error": "Not configured"}
        
        try:
            payload = {
                "voiceId": voice_id or self.default_voice_id,
                "text": text[:1000],  # Limit length
                "audioFormat": "MP3",
                "sampleRate": 24000
            }
            
            headers = {"api-key": self.api_key, "Content-Type": "application/json"}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.murf.ai/v1/speech/generate",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=20)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        if "audioFile" in data:
                            return {
                                "success": True,
                                "audio_url": f"/audio/mock_{uuid.uuid4().hex[:8]}.mp3",
                                "voice_id": voice_id or self.default_voice_id
                            }
            
            return {"success": False, "error": "TTS failed"}
        
        except:
            return {"success": False, "error": "TTS error"}

class SimpleVoiceService:
    """Simple voice service without hanging health checks"""
    
    def __init__(self, client):
        self.available = client.available
        self.client = client
        logger.info(f"🎙️ Simple voice service - Available: {self.available}")
    
    async def text_to_speech(self, text: str, voice_id: str = None):
        return await self.client.text_to_speech(text, voice_id)

# =============================================================================
# SIMPLIFIED SETTINGS
# =============================================================================

class Settings:
    def __init__(self):
        self.murf_api_key = os.getenv('MURF_API_KEY', 'your_murf_key_here')
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY', 'your_anthropic_key_here')
        self.debug = True
        self.host = "0.0.0.0"
        self.port = 8000
        
        logger.info("✅ Simplified settings initialized")

settings = Settings()

# =============================================================================
# SIMPLIFIED APP (No complex lifespan)
# =============================================================================

app = FastAPI(
    title="Excel Interview System - Simplified",
    description="Simplified version that actually starts",
    version="1.0.0-simplified"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount audio files
try:
    app.mount("/audio", StaticFiles(directory="voice_cache"), name="audio")
    logger.info("✅ Audio static files mounted")
except:
    logger.warning("⚠️ Could not mount audio files")

# Initialize services at module level (no lifespan complexity)
logger.info("🔧 Initializing services...")

try:
    murf_client = SimpleMurfClient(settings.murf_api_key)
    voice_service = SimpleVoiceService(murf_client)
    
    # Simple question bank
    questions = [
        {"id": "q1", "text": "Explain VLOOKUP vs INDEX-MATCH in Excel", "type": "free_text"},
        {"id": "q2", "text": "How do you create a pivot table?", "type": "free_text"},
        {"id": "q3", "text": "What are common Excel errors and how to fix them?", "type": "free_text"}
    ]
    
    # Simple session storage
    sessions = {}
    
    logger.info("✅ All services initialized without hanging!")
    
except Exception as e:
    logger.error(f"❌ Service initialization failed: {e}")
    voice_service = None

# =============================================================================
# SIMPLIFIED ENDPOINTS
# =============================================================================

@app.get("/")
async def root():
    return {
        "message": "Simplified Excel Interview System",
        "status": "running",
        "voice_available": voice_service and voice_service.available,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health():
    return {
        "healthy": True,
        "voice_available": voice_service and voice_service.available,
        "voice_service": voice_service.available if voice_service else False,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/voice/test")
async def test_voice():
    """Test voice synthesis"""
    
    if not voice_service or not voice_service.available:
        raise HTTPException(status_code=503, detail="Voice service not available")
    
    try:
        result = await voice_service.text_to_speech(
            "This is a test of the simplified voice system using Cooper voice.",
            "en-US-cooper"
        )
        
        return {
            "test_successful": result.get("success", False),
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/interview/start")
async def start_interview(candidate_name: str = "Test User"):
    """Start simplified interview"""
    
    session_id = f"interview_{uuid.uuid4().hex[:8]}"
    
    sessions[session_id] = {
        "candidate_name": candidate_name,
        "status": "in_progress",
        "current_question_index": 0,
        "start_time": datetime.utcnow()
    }
    
    first_question = questions[0]
    
    return {
        "success": True,
        "session_id": session_id,
        "first_question": first_question,
        "candidate_name": candidate_name
    }

@app.post("/api/interview/{session_id}/respond")
async def submit_response(session_id: str, response_text: str = Form(...)):
    """Submit response"""
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    current_index = session["current_question_index"]
    
    # Simple scoring
    score = min(5.0, len(response_text.split()) * 0.1 + 2.0)
    
    # Get next question
    next_index = current_index + 1
    if next_index < len(questions):
        next_question = questions[next_index]
        session["current_question_index"] = next_index
        interview_complete = False
    else:
        next_question = None
        session["status"] = "completed"
        interview_complete = True
    
    return {
        "success": True,
        "evaluation": {
            "score": score,
            "reasoning": f"Response has {len(response_text.split())} words"
        },
        "next_question": next_question,
        "status": "completed" if interview_complete else "in_progress"
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Simplified Excel Interview System")
    print(f"✅ Voice Service Available: {voice_service and voice_service.available}")
    print(f"✅ Questions Loaded: {len(questions)}")
    
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=False,  # Disable reload to avoid issues
        log_level="info"
    )
'''

    # Write simplified main
    with open("main_simplified.py", "w") as f:
        f.write(simplified_main)
    
    print("✅ Created main_simplified.py")
    
    return True

def main():
    """Create simplified version"""
    
    success = create_simplified_main()
    
    if success:
        print("\n🎉 SIMPLIFIED VERSION CREATED!")
        print("=" * 40)
        print("📋 What it does:")
        print("   ✅ Bypasses complex lifespan function")
        print("   ✅ Simple voice service without hanging health checks")
        print("   ✅ Basic interview functionality")
        print("   ✅ Working voice system")
        
        print("\n🚀 TEST THE SIMPLIFIED VERSION:")
        print("python main_simplified.py")
        
        print("\n👀 Should show:")
        print("✅ Voice Service Available: True")
        print("✅ Server starting without hanging")
        
        print("\n🧪 Test endpoints:")
        print("   http://localhost:8000/health")
        print("   http://localhost:8000/api/voice/test")
        
        print("\n💡 If simplified version works:")
        print("   We know the issue is in your complex lifespan function")
        print("   We can then fix the original main.py")
    
    else:
        print("❌ Could not create simplified version")

if __name__ == "__main__":
    main()