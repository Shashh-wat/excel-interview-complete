# test_voice_fix.py - Test the Voice System Fix
"""
Run this to test if the voice system fix worked
"""

import asyncio
import os
from pathlib import Path

async def test_voice_fix():
    print("🧪 Testing Voice System Fix")
    print("=" * 40)
    
    try:
        # Import the fixed components
        from voice_fix_integration import initialize_working_voice_system
        
        # Get API key
        api_key = os.getenv('MURF_API_KEY', 'your_murf_key_here')
        
        print(f"🔑 Using API key: {api_key[:15]}..." if api_key else "❌ No API key")
        
        # Initialize fixed system
        murf_client, voice_service = initialize_working_voice_system(api_key)
        
        if voice_service.available:
            print("✅ Voice service is available!")
            
            # Test TTS
            result = await voice_service.text_to_speech(
                "Testing the fixed voice system! This should work now.",
                "en-US-sarah"
            )
            
            if result["success"]:
                print("🎉 SUCCESS! Voice synthesis is working!")
                print(f"   Audio file: {result['audio_path']}")
                
                # Check if file exists
                if Path(result['audio_path']).exists():
                    file_size = Path(result['audio_path']).stat().st_size
                    print(f"   File size: {file_size} bytes")
                    print("✅ Audio file created successfully!")
                else:
                    print("❌ Audio file not found")
            else:
                print(f"❌ TTS failed: {result['error']}")
                print("📝 Check your Murf API key and internet connection")
        else:
            print("❌ Voice service not available")
            print("📝 Check your MURF_API_KEY environment variable")
        
        # Show detailed stats
        print(f"\n📊 Murf Client Stats:")
        client_stats = murf_client.get_stats()
        for key, value in client_stats.items():
            print(f"   {key}: {value}")
        
        print(f"\n📊 Voice Service Stats:")
        service_stats = voice_service.get_service_stats()
        for key, value in service_stats.items():
            print(f"   {key}: {value}")
        
        return voice_service.available
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("📝 Make sure fixed_murf_client.py is in the same directory")
        return False
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_voice_fix())
    
    if success:
        print("\n🎉 VOICE SYSTEM FIX SUCCESSFUL!")
        print("📝 Next steps:")
        print("   1. Restart your server: python main.py")
        print("   2. Test at: http://localhost:8000/api/voice/test")
        print("   3. Check health: http://localhost:8000/health")
    else:
        print("\n❌ Voice system still has issues")
        print("📝 Check the error messages above")
