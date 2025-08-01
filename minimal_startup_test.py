# minimal_startup_test.py - Find Where Startup Hangs
"""
Tests each part of the startup process to find where it hangs
"""

import asyncio
import logging
import sys
import signal
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def timeout_handler(signum, frame):
    """Handle timeout"""
    print(f"\n❌ TIMEOUT! Process hung at: {datetime.now()}")
    sys.exit(1)

async def test_voice_system_creation():
    """Test creating voice system components"""
    
    print("🎙️ Testing voice system creation...")
    
    try:
        # Import and create with timeout
        from main import MurfAPIClient, VoiceService, Settings
        
        print("   ✓ Imports successful")
        
        settings = Settings()
        print("   ✓ Settings created")
        
        print(f"   API Key: {settings.murf_api_key[:15]}...")
        
        murf_client = MurfAPIClient(settings.murf_api_key)
        print(f"   ✓ MurfAPIClient created - Available: {murf_client.available}")
        print(f"   ✓ Default voice: {murf_client.default_voice_id}")
        
        voice_service = VoiceService(murf_client)
        print(f"   ✓ VoiceService created - Available: {voice_service.available}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_orchestrator_creation():
    """Test creating orchestrator"""
    
    print("\n🎭 Testing orchestrator creation...")
    
    try:
        from main import Settings
        from interview_orchestrator import VoiceEnhancedInterviewOrchestrator
        from evaluation_engine import ClaudeEvaluationEngine
        
        print("   ✓ Orchestrator imports successful")
        
        settings = Settings()
        
        # Create evaluation engine
        evaluation_engine = ClaudeEvaluationEngine(settings.anthropic_api_key)
        print("   ✓ Evaluation engine created")
        
        # This might be where it hangs - let's see
        print("   Creating orchestrator... (this might hang)")
        
        # Set a shorter timeout for this test
        orchestrator = VoiceEnhancedInterviewOrchestrator(
            evaluation_engine=evaluation_engine
        )
        print("   ✓ Orchestrator created")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_health_checks():
    """Test health checks that might hang"""
    
    print("\n🏥 Testing health checks...")
    
    try:
        from main import MurfAPIClient, VoiceService, Settings
        
        settings = Settings()
        murf_client = MurfAPIClient(settings.murf_api_key)
        voice_service = VoiceService(murf_client)
        
        print("   Testing voice health check... (might hang here)")
        
        # This is likely where it hangs
        health_result = await asyncio.wait_for(
            voice_service.health_check(), 
            timeout=10.0  # 10 second timeout
        )
        
        print(f"   ✓ Health check result: {health_result.get('healthy', False)}")
        
        return True
        
    except asyncio.TimeoutError:
        print("   ❌ Health check TIMED OUT - this is where it hangs!")
        return False
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        return False

async def main():
    """Main test process"""
    
    print("🔍 FINDING WHERE STARTUP HANGS")
    print("=" * 50)
    
    # Set global timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(60)  # 60 second total timeout
    
    try:
        # Test 1: Voice system creation
        voice_ok = await test_voice_system_creation()
        
        if not voice_ok:
            print("❌ Voice system creation failed")
            return
        
        # Test 2: Health check (likely culprit)
        health_ok = await test_health_checks()
        
        if not health_ok:
            print("❌ Health check is where it hangs!")
            print("\n💡 SOLUTION:")
            print("   The health check is timing out")
            print("   We need to disable or fix the health check")
            return
        
        # Test 3: Orchestrator creation
        orchestrator_ok = await test_orchestrator_creation()
        
        if not orchestrator_ok:
            print("❌ Orchestrator creation failed")
            return
        
        print("\n✅ All components created successfully!")
        print("   The hang must be elsewhere in the lifespan function")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        signal.alarm(0)  # Cancel timeout

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Failed: {e}")