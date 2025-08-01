# main_production.py - YOUR REAL SYSTEM FOR DEPLOYMENT
"""
Production deployment of YOUR sophisticated interview orchestrator and evaluation engine
This integrates all your actual components:
- ClaudeEvaluationEngine with Anthropic AI
- VoiceEnhancedInterviewOrchestrator 
- FixedMurfAPIClient with real voice synthesis
- Complete session management and file analysis
"""

import asyncio
import logging
import uuid
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Import YOUR actual components
try:
    from evaluation_engine import ClaudeEvaluationEngine
    EVALUATION_ENGINE_AVAILABLE = True
    print("✅ ClaudeEvaluationEngine imported successfully")
except ImportError as e:
    EVALUATION_ENGINE_AVAILABLE = False
    print(f"❌ ClaudeEvaluationEngine import failed: {e}")

try:
    from interview_orchestrator import (
        VoiceEnhancedInterviewOrchestrator, 
        InterviewOrchestrator,
        SimpleQuestionBank
    )
    ORCHESTRATOR_AVAILABLE = True
    print("✅ InterviewOrchestrator imported successfully")
except ImportError as e:
    ORCHESTRATOR_AVAILABLE = False
    print(f"❌ InterviewOrchestrator import failed: {e}")

try:
    from fixed_murf_client import FixedMurfAPIClient, FixedVoiceService
    VOICE_CLIENT_AVAILABLE = True
    print("✅ FixedMurfClient imported successfully")
except ImportError as e:
    VOICE_CLIENT_AVAILABLE = False
    print(f"❌ FixedMurfClient import failed: {e}")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# PRODUCTION CONFIGURATION
# =============================================================================

class ProductionConfig:
    """Production configuration with environment variables"""
    
    def __init__(self):
        # API Keys from environment (no hardcoded secrets!)
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.murf_api_key = os.getenv('MURF_API_KEY') 
        
        # Server configuration
        self.host = "0.0.0.0"
        self.port = int(os.getenv('PORT', 8000))
        self.environment = os.getenv('ENVIRONMENT', 'production')
        self.debug = os.getenv('DEBUG', 'false').lower() == 'true'
        
        # Feature flags
        self.enable_voice = os.getenv('ENABLE_VOICE', 'true').lower() == 'true'
        self.enable_file_upload = os.getenv('ENABLE_FILE_UPLOAD', 'true').lower() == 'true'
        self.enable_ai_evaluation = os.getenv('ENABLE_AI_EVALUATION', 'true').lower() == 'true'
        
        # Validate configuration
        self.claude_available = bool(self.anthropic_api_key and len(self.anthropic_api_key) > 10)
        self.voice_available = bool(self.murf_api_key and len(self.murf_api_key) > 10)
        
        logger.info(f"🔧 Production config loaded:")
        logger.info(f"   Environment: {self.environment}")
        logger.info(f"   Claude API: {'✅' if self.claude_available else '❌'}")
        logger.info(f"   Voice API: {'✅' if self.voice_available else '❌'}")
        logger.info(f"   Debug: {self.debug}")

config = ProductionConfig()

# =============================================================================
# INITIALIZE YOUR REAL SYSTEM COMPONENTS
# =============================================================================

async def initialize_production_system():
    """Initialize YOUR complete production system"""
    
    logger.info("🚀 Initializing YOUR production interview system...")
    
    # Initialize evaluation engine (YOUR ClaudeEvaluationEngine)
    evaluation_engine = None
    if EVALUATION_ENGINE_AVAILABLE and config.claude_available:
        try:
            evaluation_engine = ClaudeEvaluationEngine(
                anthropic_api_key=config.anthropic_api_key
            )
            logger.info("✅ YOUR ClaudeEvaluationEngine initialized")
        except Exception as e:
            logger.error(f"❌ ClaudeEvaluationEngine failed: {e}")
    
    # Initialize voice service (YOUR FixedMurfClient)
    voice_service = None
    if VOICE_CLIENT_AVAILABLE and config.voice_available:
        try:
            murf_client = FixedMurfAPIClient(config.murf_api_key)
            voice_service = FixedVoiceService(murf_client)
            logger.info("✅ YOUR FixedVoiceService initialized")
        except Exception as e:
            logger.error(f"❌ FixedVoiceService failed: {e}")
    
    # Initialize question bank
    question_bank = SimpleQuestionBank()
    
    # Initialize YOUR interview orchestrator
    orchestrator = None
    if ORCHESTRATOR_AVAILABLE:
        try:
            if voice_service and config.enable_voice:
                orchestrator = VoiceEnhancedInterviewOrchestrator(
                    evaluation_engine=evaluation_engine,
                    question_bank=question_bank,
                    voice_service=voice_service
                )
                logger.info("✅ YOUR VoiceEnhancedInterviewOrchestrator initialized")
            else:
                orchestrator = InterviewOrchestrator(
                    evaluation_engine=evaluation_engine,
                    question_bank=question_bank
                )
                logger.info("✅ YOUR InterviewOrchestrator initialized")
        except Exception as e:
            logger.error(f"❌ InterviewOrchestrator failed: {e}")
    
    if not orchestrator:
        raise Exception("Failed to initialize interview orchestrator")
    
    logger.info("🎉 YOUR complete production system initialized!")
    return {
        "orchestrator": orchestrator,
        "evaluation_engine": evaluation_engine,
        "voice_service": voice_service,
        "question_bank": question_bank
    }

# =============================================================================
# FASTAPI APP WITH YOUR REAL SYSTEM
# =============================================================================

app = FastAPI(
    title="Excel Interview System - YOUR PRODUCTION VERSION",
    description="Production deployment of YOUR sophisticated interview orchestrator",
    version="1.0.0-production"
)

# CORS
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
Path("logs").mkdir(exist_ok=True)

# Mount static files
try:
    app.mount("/audio", StaticFiles(directory="voice_cache"), name="audio")
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
except Exception as e:
    logger.warning(f"Static files mount failed: {e}")

# Global system components (will be initialized on startup)
orchestrator = None
evaluation_engine = None
voice_service = None

# =============================================================================
# STARTUP EVENT
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize YOUR production system on startup"""
    global orchestrator, evaluation_engine, voice_service
    
    try:
        system_components = await initialize_production_system()
        orchestrator = system_components["orchestrator"]
        evaluation_engine = system_components["evaluation_engine"]
        voice_service = system_components["voice_service"]
        
        logger.info("🎉 YOUR production system startup complete!")
        
    except Exception as e:
        logger.error(f"❌ Production startup failed: {e}")
        # Don't exit - let health checks show the issues

# =============================================================================
# API ENDPOINTS USING YOUR REAL SYSTEM
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint showing YOUR system status"""
    return {
        "message": "Excel Interview System - YOUR PRODUCTION VERSION",
        "status": "running",
        "components": {
            "orchestrator_available": orchestrator is not None,
            "evaluation_engine_available": evaluation_engine is not None,
            "voice_service_available": voice_service is not None and voice_service.available,
            "claude_evaluation": config.claude_available,
            "murf_voice": config.voice_available
        },
        "system_stats": orchestrator.get_system_stats() if orchestrator else {},
        "voice_stats": voice_service.get_service_stats() if voice_service else {},
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Comprehensive health check of YOUR system"""
    
    health_data = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "orchestrator": orchestrator is not None,
            "evaluation_engine": evaluation_engine is not None,
            "voice_service": voice_service is not None,
            "question_bank": True
        },
        "api_services": {
            "anthropic_claude": config.claude_available,
            "murf_voice": config.voice_available
        },
        "performance": {}
    }
    
    # Add performance stats if available
    if orchestrator:
        health_data["performance"]["orchestrator"] = orchestrator.get_system_stats()
    
    if evaluation_engine and hasattr(evaluation_engine, 'claude_api'):
        health_data["performance"]["claude_api"] = evaluation_engine.claude_api.get_performance_stats()
    
    if voice_service:
        health_data["performance"]["voice_service"] = voice_service.get_service_stats()
    
    # Determine overall health
    critical_components = ["orchestrator", "evaluation_engine"]
    if not all(health_data["components"][comp] for comp in critical_components):
        health_data["status"] = "degraded"
    
    return health_data

@app.post("/api/interview/start")
async def start_interview(request: Request):
    """Start interview using YOUR orchestrator"""
    
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Interview orchestrator not available")
    
    try:
        body = await request.json()
        candidate_name = body.get("candidate_name", "Anonymous")
        skill_level = body.get("skill_level", "intermediate")
        voice_enabled = body.get("voice_enabled", True)
        
        # Use YOUR orchestrator
        if voice_enabled and isinstance(orchestrator, VoiceEnhancedInterviewOrchestrator):
            result = await orchestrator.start_voice_interview(
                candidate_name=candidate_name,
                voice_id=body.get("voice_id", "en-US-cooper")
            )
        else:
            result = await orchestrator.start_interview(
                candidate_name=candidate_name,
                skill_level=skill_level
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Start interview failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/interview/{session_id}/respond")
async def submit_response(session_id: str, request: Request):
    """Submit response using YOUR evaluation engine"""
    
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Interview orchestrator not available")
    
    try:
        body = await request.json()
        response_text = body.get("response_text", "").strip()
        time_taken = body.get("time_taken", 0)
        
        if not response_text:
            raise HTTPException(status_code=400, detail="Response text required")
        
        # Use YOUR orchestrator's evaluation
        if isinstance(orchestrator, VoiceEnhancedInterviewOrchestrator):
            result = await orchestrator.submit_voice_response(
                session_id=session_id,
                response_text=response_text,
                time_taken=time_taken
            )
        else:
            result = await orchestrator.submit_response(
                session_id=session_id,
                response_text=response_text,
                time_taken=time_taken
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Submit response failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/interview/{session_id}/upload")
async def upload_file(session_id: str, file: UploadFile = File(...)):
    """Handle file uploads using YOUR file analyzer"""
    
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Interview orchestrator not available")
    
    if not config.enable_file_upload:
        raise HTTPException(status_code=503, detail="File upload disabled")
    
    try:
        # Save uploaded file
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        file_path = upload_dir / f"{session_id}_{file.filename}"
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Use YOUR evaluation engine for file analysis
        if evaluation_engine:
            # Get current question for context
            session_status = await orchestrator.get_session_status(session_id)
            if session_status.get("success"):
                # Evaluate file with YOUR engine
                session_data = orchestrator.sessions.get(session_id, {})
                current_question = session_data.get("current_question", {})
                
                evaluation = await evaluation_engine.evaluate_response(
                    question=current_question,
                    text_response=None,
                    file_path=str(file_path)
                )
                
                return {
                    "success": True,
                    "file_path": str(file_path),
                    "filename": file.filename,
                    "evaluation": evaluation,
                    "message": "File analyzed using YOUR evaluation engine"
                }
        
        return {
            "success": True,
            "file_path": str(file_path),
            "filename": file.filename,
            "message": "File uploaded successfully"
        }
        
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/interview/{session_id}/status")
async def get_interview_status(session_id: str):
    """Get status using YOUR orchestrator"""
    
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Interview orchestrator not available")
    
    try:
        result = await orchestrator.get_session_status(session_id)
        return result
        
    except Exception as e:
        logger.error(f"Get status failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/interview/{session_id}/report")
async def generate_report(session_id: str):
    """Generate report using YOUR orchestrator"""
    
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Interview orchestrator not available")
    
    try:
        report = await orchestrator.generate_final_report(session_id)
        
        return {
            "success": True,
            "session_id": session_id,
            "report": report,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/voice/synthesize")
async def synthesize_speech(request: Request):
    """Voice synthesis using YOUR FixedMurfClient"""
    
    if not voice_service or not voice_service.available:
        raise HTTPException(status_code=503, detail="Voice service not available")
    
    try:
        body = await request.json()
        text = body.get("text", "")
        voice_id = body.get("voice_id", "en-US-cooper")
        
        if not text:
            raise HTTPException(status_code=400, detail="Text required")
        
        # Use YOUR voice service
        result = await voice_service.text_to_speech(text, voice_id)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/voice/test")
async def test_voice():
    """Test YOUR voice system"""
    
    if not voice_service:
        raise HTTPException(status_code=503, detail="Voice service not initialized")
    
    try:
        health_check = await voice_service.health_check()
        
        if health_check.get("healthy"):
            test_result = await voice_service.text_to_speech(
                "This is a test of YOUR production voice system using the Murf API.",
                "en-US-cooper"
            )
            
            return {
                "test_successful": test_result.get("success", False),
                "health_check": health_check,
                "test_result": test_result,
                "service_stats": voice_service.get_service_stats()
            }
        else:
            return {
                "test_successful": False,
                "health_check": health_check,
                "error": "Voice service health check failed"
            }
            
    except Exception as e:
        logger.error(f"Voice test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sessions")
async def list_sessions():
    """List sessions using YOUR orchestrator"""
    
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Interview orchestrator not available")
    
    try:
        result = await orchestrator.get_all_sessions()
        return result
        
    except Exception as e:
        logger.error(f"List sessions failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system/stats")
async def get_system_stats():
    """Get comprehensive stats from YOUR system"""
    
    stats = {
        "timestamp": datetime.utcnow().isoformat(),
        "orchestrator_stats": orchestrator.get_system_stats() if orchestrator else {},
        "voice_stats": voice_service.get_service_stats() if voice_service else {},
        "configuration": {
            "environment": config.environment,
            "claude_available": config.claude_available,
            "voice_available": config.voice_available,
            "file_upload_enabled": config.enable_file_upload
        }
    }
    
    # Add evaluation engine stats if available
    if evaluation_engine and hasattr(evaluation_engine, 'claude_api'):
        stats["evaluation_stats"] = evaluation_engine.claude_api.get_performance_stats()
    
    # Add cache stats if available
    if evaluation_engine and hasattr(evaluation_engine, 'cache'):
        stats["cache_stats"] = evaluation_engine.cache.get_cache_stats()
    
    return stats

# =============================================================================
# PRODUCTION STARTUP
# =============================================================================

def main():
    """Production startup using YOUR system"""
    
    print("🚀 STARTING YOUR PRODUCTION EXCEL INTERVIEW SYSTEM")
    print("=" * 60)
    print("🎯 Features:")
    print("  ✅ YOUR ClaudeEvaluationEngine (AI-powered)")
    print("  ✅ YOUR VoiceEnhancedInterviewOrchestrator")
    print("  ✅ YOUR FixedMurfAPIClient (real voice)")
    print("  ✅ YOUR ExcelFileAnalyzer")
    print("  ✅ Production configuration")
    print("=" * 60)
    
    # Validate critical components
    if not ORCHESTRATOR_AVAILABLE:
        print("❌ CRITICAL: interview_orchestrator.py not found!")
        print("   Make sure interview_orchestrator.py is in your project directory")
        sys.exit(1)
    
    if not EVALUATION_ENGINE_AVAILABLE and config.enable_ai_evaluation:
        print("⚠️ WARNING: evaluation_engine.py not found - using fallback")
    
    if not VOICE_CLIENT_AVAILABLE and config.enable_voice:
        print("⚠️ WARNING: fixed_murf_client.py not found - voice disabled")
    
    print(f"🌐 Starting server on {config.host}:{config.port}")
    print(f"🔧 Environment: {config.environment}")
    print("=" * 60)
    
    try:
        import uvicorn
        
        uvicorn.run(
            app,
            host=config.host,
            port=config.port,
            log_level="info" if not config.debug else "debug",
            reload=False,  # Disable in production
            access_log=True
        )
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down YOUR production system...")
    except Exception as e:
        print(f"\n❌ Server failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)