# final_voice_test.py - Final Voice System Test
"""
Test the completely fixed voice system with correct voice ID and sample rate
"""

import asyncio
import os
from pathlib import Path

async def test_complete_system():
    """Test the complete fixed voice system"""
    
    print("🎉 FINAL VOICE SYSTEM TEST")
    print("=" * 50)
    
    try:
        # Import the fixed system
        from fixed_murf_client import FixedMurfAPIClient, FixedVoiceService
        
        # Get API key
        api_key = os.getenv('MURF_API_KEY', 'your_murf_key_here')
        print(f"🔑 API Key: {api_key[:15]}...")
        
        # Create components
        print("🔧 Creating voice system components...")
        murf_client = FixedMurfAPIClient(api_key)
        voice_service = FixedVoiceService(murf_client)
        
        print(f"   Murf Client Available: {murf_client.available}")
        print(f"   Voice Service Available: {voice_service.available}")
        print(f"   Default Voice ID: {murf_client.default_voice_id}")
        
        if not voice_service.available:
            print("❌ Voice service not available")
            return False
        
        # Test 1: Short text
        print("\n🧪 Test 1: Short text synthesis...")
        result1 = await voice_service.text_to_speech(
            "Hello! Voice system test.",
            "natalie"
        )
        
        if result1["success"]:
            print("✅ Short text: SUCCESS!")
            print(f"   Audio file: {result1['audio_path']}")
            print(f"   File exists: {Path(result1['audio_path']).exists()}")
            print(f"   File size: {Path(result1['audio_path']).stat().st_size} bytes")
        else:
            print(f"❌ Short text failed: {result1['error']}")
            return False
        
        # Test 2: Interview question
        print("\n🧪 Test 2: Interview question synthesis...")
        interview_text = "Explain the difference between VLOOKUP and INDEX-MATCH functions in Excel. When would you use each one?"
        
        result2 = await voice_service.text_to_speech(interview_text, "natalie")
        
        if result2["success"]:
            print("✅ Interview question: SUCCESS!")
            print(f"   Audio file: {result2['audio_path']}")
            print(f"   File size: {Path(result2['audio_path']).stat().st_size} bytes")
        else:
            print(f"❌ Interview question failed: {result2['error']}")
            return False
        
        # Test 3: Feedback text
        print("\n🧪 Test 3: Feedback synthesis...")
        feedback_text = "Excellent response! Your score is 4.2 out of 5. You demonstrated strong understanding of Excel lookup functions."
        
        result3 = await voice_service.text_to_speech(feedback_text, "natalie")
        
        if result3["success"]:
            print("✅ Feedback synthesis: SUCCESS!")
            print(f"   Audio file: {result3['audio_path']}")
        else:
            print(f"❌ Feedback synthesis failed: {result3['error']}")
            return False
        
        # Show stats
        print("\n📊 System Statistics:")
        client_stats = murf_client.get_stats()
        service_stats = voice_service.get_service_stats()
        
        print(f"   API Requests: {client_stats['requests_made']}")
        print(f"   Successful: {client_stats['successful_requests']}")
        print(f"   Success Rate: {client_stats['success_rate_percentage']}%")
        print(f"   Audio Files Created: {client_stats['audio_files_created']}")
        print(f"   Cache Files: {client_stats['cache_files_count']}")
        
        print("\n🎉 ALL TESTS PASSED!")
        print("🎯 Your voice system is now 100% working!")
        
        return True
        
    except Exception as e:
        print(f"❌ System test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def verify_server_integration():
    """Verify the voice system works with your server"""
    
    print("\n🔗 Testing server integration...")
    
    try:
        # Test if server is running
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get("http://localhost:8000/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        health_data = await response.json()
                        voice_synthesis = health_data.get("features", {}).get("voice_synthesis", False)
                        
                        print(f"✅ Server is running")
                        print(f"   Voice synthesis enabled: {voice_synthesis}")
                        
                        if voice_synthesis:
                            print("🎉 Server already has working voice system!")
                        else:
                            print("⚠️ Server needs restart to use fixed voice system")
                            
                        return True
                    else:
                        print(f"⚠️ Server responded with status {response.status}")
                        return False
            except:
                print("⚠️ Server not running - restart needed")
                return False
                
    except Exception as e:
        print(f"⚠️ Could not test server: {e}")
        return False

async def main():
    """Main test execution"""
    
    # Test the complete system
    system_working = await test_complete_system()
    
    if system_working:
        # Test server integration
        await verify_server_integration()
        
        print("\n🚀 VOICE SYSTEM READY!")
        print("=" * 50)
        print("📋 What's working:")
        print("   ✅ Murf API connection")
        print("   ✅ Voice ID: natalie") 
        print("   ✅ Audio generation")
        print("   ✅ File storage")
        print("   ✅ Service integration")
        
        print("\n📋 Next steps:")
        print("   1. Restart your server: python main.py")
        print("   2. Look for ✅ Voice service in startup logs")
        print("   3. Test at: http://localhost:8000/api/voice/test")
        print("   4. Your interviews will now have working voice!")
        
    else:
        print("\n❌ System still has issues")
        print("📝 Debug steps:")
        print("   1. Check the error messages above")
        print("   2. Verify Murf account has API access")
        print("   3. Test manually at https://murf.ai")

if __name__ == "__main__":
    asyncio.run(main())