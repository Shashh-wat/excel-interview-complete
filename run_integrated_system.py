# run_integrated_system.py - Complete System Integration Runner
"""
This script runs your complete Excel Interview System with all components integrated.
It handles missing dependencies gracefully and provides a working system.

Usage:
    python run_integrated_system.py

This will:
1. Check for all required components
2. Initialize with fallbacks where needed
3. Run the complete interview system
4. Provide a working API endpoint
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# SYSTEM CHECKER
# =============================================================================

def check_system_components():
    """Check which components are available"""
    
    components_status = {
        "main.py": False,
        "evaluation_engine.py": False,
        "interview_orchestrator.py": False,
        "question_bank_db.py": False,
        "models.py": False,
        "config.py": False,
        "missing_components.py": False
    }
    
    print("🔍 Checking system components...")
    
    for component in components_status.keys():
        if Path(component).exists():
            components_status[component] = True
            print(f"✅ {component} - Found")
        else:
            print(f"❌ {component} - Missing")
    
    return components_status

# =============================================================================
# SYSTEM INITIALIZER
# =============================================================================

class IntegratedSystemRunner:
    """Main system runner that integrates all components"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.components = {}
        self.system_ready = False
        
    async def initialize_system(self):
        """Initialize the complete system"""
        
        print("🚀 INITIALIZING EXCEL INTERVIEW SYSTEM")
        print("=" * 60)
        
        # Check components
        component_status = check_system_components()
        
        # Try to import and initialize components
        await self._initialize_components(component_status)
        
        # Create integrated system
        await self._create_integrated_system()
        
        return self.system_ready
    
    async def _initialize_components(self, component_status):
        """Initialize individual components"""
        
        print("\n📦 Initializing components...")
        
        # 1. Models (for data structures)
        try:
            if component_status["models.py"]:
                import models
                print("✅ Models loaded from models.py")
            else:
                from missing_components import SkillCategory, DifficultyLevel, QuestionType
                print("⚠️ Using fallback models")
        except Exception as e:
            print(f"❌ Models initialization failed: {e}")
        
        # 2. Evaluation Engine
        try:
            if component_status["evaluation_engine.py"]:
                from evaluation_engine import ClaudeEvaluationEngine
                self.components["evaluation_engine"] = ClaudeEvaluationEngine()
                print("✅ Evaluation engine loaded")
            else:
                from missing_components import FallbackEvaluationEngine
                self.components["evaluation_engine"] = FallbackEvaluationEngine()
                print("⚠️ Using fallback evaluation engine")
        except Exception as e:
            print(f"❌ Evaluation engine failed: {e}")
            from missing_components import FallbackEvaluationEngine
            self.components["evaluation_engine"] = FallbackEvaluationEngine()
        
        # 3. Voice Service
        try:
            if component_status["main.py"]:
                from main import VoiceService, MurfAPIClient
                murf_client = MurfAPIClient("test_key")
                self.components["voice_service"] = VoiceService(murf_client)
                print("✅ Voice service loaded from main.py")
            else:
                from missing_components import FallbackVoiceService
                self.components["voice_service"] = FallbackVoiceService()
                print("⚠️ Using fallback voice service")
        except Exception as e:
            print(f"❌ Voice service failed: {e}")
            from missing_components import FallbackVoiceService
            self.components["voice_service"] = FallbackVoiceService()
        
        # 4. Question Bank
        try:
            if component_status["question_bank_db.py"]:
                from question_bank_db import QuestionBankFactory
                self.components["question_bank"] = await QuestionBankFactory.create_enhanced_question_bank()
                print("✅ Enhanced question bank loaded")
            else:
                from missing_components import SimpleQuestionBank
                self.components["question_bank"] = SimpleQuestionBank()
                print("⚠️ Using simple question bank")
        except Exception as e:
            print(f"❌ Question bank failed: {e}")
            from missing_components import SimpleQuestionBank
            self.components["question_bank"] = SimpleQuestionBank()
        
        # 5. Interview Orchestrator
        try:
            if component_status["interview_orchestrator.py"]:
                from interview_orchestrator import InterviewOrchestrator
                self.components["orchestrator"] = InterviewOrchestrator(
                    evaluation_engine=self.components["evaluation_engine"],
                    question_bank=self.components["question_bank"]
                )
                print("✅ Interview orchestrator loaded")
            else:
                self.components["orchestrator"] = self._create_basic_orchestrator()
                print("⚠️ Using basic orchestrator")
        except Exception as e:
            print(f"❌ Orchestrator failed: {e}")
            self.components["orchestrator"] = self._create_basic_orchestrator()
    
    def _create_basic_orchestrator(self):
        """Create a basic orchestrator if the main one isn't available"""
        
        class BasicOrchestrator:
            def __init__(self, evaluation_engine, question_bank):
                self.evaluation_engine = evaluation_engine
                self.question_bank = question_bank
                self.sessions = {}
            
            async def start_interview(self, candidate_name=None):
                session_id = f"interview_{len(self.sessions)}_{asyncio.get_event_loop().time()}"
                
                question = await self.question_bank.get_question()
                if question:
                    question_dict = question.to_dict() if hasattr(question, 'to_dict') else question.__dict__
                    
                    self.sessions[session_id] = {
                        "candidate_name": candidate_name,
                        "status": "in_progress",
                        "current_question": question_dict,
                        "questions_asked": [],
                        "evaluations": []
                    }
                    
                    return {
                        "success": True,
                        "session_id": session_id,
                        "first_question": question_dict,
                        "candidate_name": candidate_name
                    }
                
                return {"success": False, "error": "No questions available"}
            
            async def submit_response(self, session_id, response_text, time_taken=0):
                if session_id not in self.sessions:
                    return {"success": False, "error": "Session not found"}
                
                session = self.sessions[session_id]
                current_question = session["current_question"]
                
                # Evaluate response
                evaluation = await self.evaluation_engine.evaluate_response(
                    current_question, response_text
                )
                
                session["evaluations"].append(evaluation)
                session["questions_asked"].append(current_question.get("id"))
                
                # Get next question
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
        
        return BasicOrchestrator(
            self.components["evaluation_engine"],
            self.components["question_bank"]
        )
    
    async def _create_integrated_system(self):
        """Create the integrated system"""
        
        print("\n🔧 Creating integrated system...")
        
        try:
            # Test each component
            print("🧪 Testing components...")
            
            # Test evaluation engine
            if self.components["evaluation_engine"]:
                health = await self.components["evaluation_engine"].health_check()
                print(f"   Evaluation Engine: {health.get('status', 'unknown')}")
            
            # Test question bank
            if self.components["question_bank"]:
                status = await self.components["question_bank"].get_question_bank_status()
                print(f"   Question Bank: {status.get('initialized', False)}")
            
            # Test orchestrator
            if self.components["orchestrator"]:
                print("   Interview Orchestrator: Available")
            
            self.system_ready = True
            print("✅ Integrated system ready!")
            
        except Exception as e:
            print(f"❌ System integration failed: {e}")
            self.system_ready = False
    
    async def run_interview_demo(self):
        """Run a demonstration interview"""
        
        if not self.system_ready:
            print("❌ System not ready")
            return False
        
        print("\n🎯 RUNNING INTERVIEW DEMONSTRATION")
        print("=" * 60)
        
        try:
            orchestrator = self.components["orchestrator"]
            
            # Start interview
            print("📝 Starting interview...")
            start_result = await orchestrator.start_interview("Demo User")
            
            if not start_result.get("success", True):
                print(f"❌ Failed to start interview: {start_result.get('error')}")
                return False
            
            session_id = start_result["session_id"]
            print(f"✅ Interview started: {session_id}")
            print(f"📋 First question: {start_result['first_question']['text']}")
            
            # Simulate responses
            demo_responses = [
                "VLOOKUP is a vertical lookup function in Excel that searches for a value in the leftmost column of a table and returns a corresponding value from a specified column in the same row. It's useful for finding data in large tables.",
                "To create a pivot table, you select your data, go to Insert > Pivot Table, choose where to place it, and then drag fields to the Rows, Columns, Values, and Filters areas. It's great for summarizing large amounts of data.",
                "Common Excel errors include #N/A which means not available, #REF! which means invalid cell reference, and #VALUE! which means wrong data type. You can use IFERROR function to handle these gracefully."
            ]
            
            for i, response in enumerate(demo_responses, 1):
                print(f"\n📝 Submitting response {i}...")
                print(f"Response: {response[:60]}...")
                
                result = await orchestrator.submit_response(
                    session_id=session_id,
                    response_text=response,
                    time_taken=45 + i * 15
                )
                
                if result.get("success", True):
                    evaluation = result.get("evaluation", {})
                    print(f"✅ Response {i} evaluated:")
                    print(f"   Score: {evaluation.get('score', 0)}/5.0")
                    print(f"   Reasoning: {evaluation.get('reasoning', 'No reasoning')[:50]}...")
                    
                    if result.get("status") == "completed":
                        print("🎉 Interview completed!")
                        break
                    elif result.get("next_question"):
                        print(f"📋 Next question: {result['next_question']['text'][:60]}...")
                else:
                    print(f"❌ Response {i} failed: {result.get('error')}")
                    break
            
            print("\n🎉 Interview demonstration completed!")
            return True
            
        except Exception as e:
            print(f"❌ Interview demo failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def run_api_server(self):
        """Run a simple API server for the interview system"""
        
        if not self.system_ready:
            print("❌ System not ready for API server")
            return False
        
        print("\n🌐 STARTING API SERVER")
        print("=" * 60)
        
        try:
            # Try to use FastAPI if available
            try:
                from fastapi import FastAPI, HTTPException
                from fastapi.middleware.cors import CORSMiddleware
                from pydantic import BaseModel
                import uvicorn
                
                app = FastAPI(
                    title="Excel Interview System",
                    description="Integrated Excel Skills Assessment API",
                    version="4.0.0-integrated"
                )
                
                app.add_middleware(
                    CORSMiddleware,
                    allow_origins=["*"],
                    allow_credentials=True,
                    allow_methods=["*"],
                    allow_headers=["*"],
                )
                
                # Request models
                class StartInterviewRequest(BaseModel):
                    candidate_name: str = "Anonymous"
                
                class SubmitResponseRequest(BaseModel):
                    response_text: str
                    time_taken_seconds: int = 0
                
                # Store orchestrator reference
                orchestrator = self.components["orchestrator"]
                
                @app.get("/")
                async def root():
                    return {
                        "message": "Excel Interview System - Integrated Version",
                        "status": "operational",
                        "features": ["AI Assessment", "Question Bank", "Session Management"],
                        "endpoints": ["/health", "/api/interview/start", "/api/interview/{session_id}/respond"]
                    }
                
                @app.get("/health")
                async def health_check():
                    return {
                        "healthy": True,
                        "system_ready": self.system_ready,
                        "components": {
                            "evaluation_engine": "available" if self.components.get("evaluation_engine") else "unavailable",
                            "voice_service": "available" if self.components.get("voice_service") else "unavailable",
                            "question_bank": "available" if self.components.get("question_bank") else "unavailable",
                            "orchestrator": "available" if self.components.get("orchestrator") else "unavailable"
                        }
                    }
                
                @app.post("/api/interview/start")
                async def start_interview(request: StartInterviewRequest):
                    try:
                        result = await orchestrator.start_interview(request.candidate_name)
                        if result.get("success", True):
                            return result
                        else:
                            raise HTTPException(status_code=500, detail=result.get("error"))
                    except Exception as e:
                        raise HTTPException(status_code=500, detail=str(e))
                
                @app.post("/api/interview/{session_id}/respond")
                async def submit_response(session_id: str, request: SubmitResponseRequest):
                    try:
                        result = await orchestrator.submit_response(
                            session_id=session_id,
                            response_text=request.response_text,
                            time_taken=request.time_taken_seconds
                        )
                        if result.get("success", True):
                            return result
                        else:
                            raise HTTPException(status_code=500, detail=result.get("error"))
                    except Exception as e:
                        raise HTTPException(status_code=500, detail=str(e))
                
                @app.get("/api/interview/{session_id}/status")
                async def get_session_status(session_id: str):
                    try:
                        if hasattr(orchestrator, 'sessions') and session_id in orchestrator.sessions:
                            session = orchestrator.sessions[session_id]
                            return {
                                "session_id": session_id,
                                "status": session.get("status"),
                                "questions_completed": len(session.get("questions_asked", [])),
                                "evaluations": session.get("evaluations", [])
                            }
                        else:
                            raise HTTPException(status_code=404, detail="Session not found")
                    except HTTPException:
                        raise
                    except Exception as e:
                        raise HTTPException(status_code=500, detail=str(e))
                
                print("✅ FastAPI server configured")
                print("📍 Starting server at http://localhost:8000")
                print("📚 API documentation: http://localhost:8000/docs")
                print("🏥 Health check: http://localhost:8000/health")
                print("\nPress Ctrl+C to stop the server")
                
                # Run server
                uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
                
            except ImportError:
                print("⚠️ FastAPI not available, starting simple HTTP server...")
                await self._run_simple_server()
        
        except Exception as e:
            print(f"❌ API server failed: {e}")
            return False
    
    async def _run_simple_server(self):
        """Run a simple HTTP server without FastAPI"""
        
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import json
        import urllib.parse
        
        orchestrator = self.components["orchestrator"]
        
        class InterviewHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/":
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    response = {
                        "message": "Excel Interview System - Simple Server",
                        "status": "operational",
                        "note": "Install FastAPI for full API functionality"
                    }
                    self.wfile.write(json.dumps(response).encode())
                elif self.path == "/health":
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    response = {"healthy": True, "server_type": "simple"}
                    self.wfile.write(json.dumps(response).encode())
                else:
                    self.send_response(404)
                    self.end_headers()
            
            def do_OPTIONS(self):
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.end_headers()
            
            def log_message(self, format, *args):
                pass  # Suppress default logging
        
        server = HTTPServer(('0.0.0.0', 8000), InterviewHandler)
        print("✅ Simple HTTP server started at http://localhost:8000")
        print("Press Ctrl+C to stop")
        
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")
            server.shutdown()
    
    def get_system_info(self):
        """Get comprehensive system information"""
        
        return {
            "system_ready": self.system_ready,
            "components": {
                name: "available" if component else "unavailable"
                for name, component in self.components.items()
            },
            "capabilities": {
                "text_evaluation": bool(self.components.get("evaluation_engine")),
                "voice_synthesis": bool(self.components.get("voice_service")),
                "question_management": bool(self.components.get("question_bank")),
                "interview_orchestration": bool(self.components.get("orchestrator"))
            }
        }

# =============================================================================
# MAIN RUNNER
# =============================================================================

async def main():
    """Main function to run the integrated system"""
    
    print("🚀 EXCEL INTERVIEW SYSTEM - INTEGRATED RUNNER")
    print("=" * 70)
    
    # Create and initialize system
    runner = IntegratedSystemRunner()
    
    success = await runner.initialize_system()
    
    if not success:
        print("❌ System initialization failed")
        return
    
    # Show system info
    info = runner.get_system_info()
    print(f"\n📊 System Information:")
    print(f"   System Ready: {info['system_ready']}")
    print(f"   Components Available:")
    for name, status in info['components'].items():
        emoji = "✅" if status == "available" else "❌"
        print(f"     {emoji} {name}")
    
    print(f"\n🎯 Capabilities:")
    for capability, available in info['capabilities'].items():
        emoji = "✅" if available else "❌"
        print(f"     {emoji} {capability}")
    
    # Ask user what to do
    print(f"\n🤔 What would you like to do?")
    print("1. Run interview demonstration")
    print("2. Start API server")
    print("3. Both (demo first, then server)")
    print("4. Exit")
    
    try:
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            await runner.run_interview_demo()
        elif choice == "2":
            await runner.run_api_server()
        elif choice == "3":
            await runner.run_interview_demo()
            input("\nPress Enter to start API server...")
            await runner.run_api_server()
        elif choice == "4":
            print("👋 Goodbye!")
        else:
            print("❌ Invalid choice")
    
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")

# =============================================================================
# STANDALONE EXECUTION
# =============================================================================

if __name__ == "__main__":
    print("🔧 Excel Interview System - Integrated Runner")
    print("This script integrates all your components and runs the complete system.")
    print("It handles missing dependencies gracefully with fallback implementations.")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 System shutdown completed")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

# =============================================================================
# USAGE INSTRUCTIONS
# =============================================================================

"""
USAGE INSTRUCTIONS:

1. Save this file as 'run_integrated_system.py' in your project directory

2. Make sure you have the missing_components.py file in the same directory

3. Run the system:
   python run_integrated_system.py

4. The system will:
   - Check which components are available
   - Initialize with fallbacks where needed
   - Offer to run a demo or start an API server

5. API Endpoints (if FastAPI is available):
   - GET  /                              - System info
   - GET  /health                        - Health check
   - POST /api/interview/start           - Start interview
   - POST /api/interview/{id}/respond    - Submit response
   - GET  /api/interview/{id}/status     - Get session status

6. Dependencies (optional, will use fallbacks if missing):
   - fastapi
   - uvicorn
   - pydantic

To install optional dependencies:
   pip install fastapi uvicorn pydantic

The system works without these dependencies but with limited API functionality.
"""