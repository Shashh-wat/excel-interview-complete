# simple_voice_test.py - Test Common Murf Voice Names
"""
Tests common Murf voice names to find one that works
Based on Murf API docs showing voice names like "natalie", "sarah", etc.
"""

import asyncio
import aiohttp
import os

async def test_murf_voice(api_key: str, voice_id: str, test_text: str = "Hello test") -> dict:
    """Test a specific voice ID with Murf API"""
    
    try:
        payload = {
            "voiceId": voice_id,
            "text": test_text,
            "audioFormat": "MP3"
        }
        
        headers = {
            "api-key": api_key,
            "Content-Type": "application/json"
        }
        
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
                        return {"success": True, "voice_id": voice_id, "audio_url": data["audioFile"]}
                
                error_text = await response.text()
                return {"success": False, "voice_id": voice_id, "error": f"{response.status}: {error_text[:100]}"}
    
    except Exception as e:
        return {"success": False, "voice_id": voice_id, "error": str(e)}

async def find_working_voice():
    """Find a working voice ID from common Murf voices"""
    
    print("🎙️ TESTING COMMON MURF VOICE NAMES")
    print("=" * 60)
    
    api_key = os.getenv('MURF_API_KEY', 'ap2_efed6cf1-51d4-4390-989b-f2c4d112dc61')
    print(f"🔑 API Key: {api_key[:15]}...")
    
    # Common Murf voice names based on documentation
    common_voices = [
        # Just names (recommended format)
        "natalie",
        "sarah", 
        "john",
        "emma",
        "mike",
        "olivia",
        "james",
        "sophia",
        "william",
        "charlotte",
        
        # Full format versions
        "en-US-natalie",
        "en-US-sarah",
        "en-US-john", 
        "en-US-emma",
        "en-US-mike",
        
        # Alternative formats
        "natalie-en-us",
        "sarah-en-us",
        "john-en-us"
    ]
    
    print(f"🧪 Testing {len(common_voices)} common voice names...")
    
    working_voices = []
    
    for voice_id in common_voices:
        print(f"   Testing: {voice_id}... ", end="")
        
        result = await test_murf_voice(api_key, voice_id, "Quick test")
        
        if result["success"]:
            print("✅ WORKS!")
            working_voices.append(voice_id)
            
            # Test with longer text to confirm
            long_test = await test_murf_voice(
                api_key, 
                voice_id, 
                "This is a longer test to confirm the voice works properly for the interview system."
            )
            
            if long_test["success"]:
                print(f"🎉 PERFECT! Voice '{voice_id}' works for both short and long text!")
                return voice_id
            else:
                print(f"⚠️ Works for short text but failed long test")
        else:
            print(f"❌ Failed: {result['error'][:50]}...")
    
    if working_voices:
        print(f"\n✅ Working voices found: {working_voices}")
        return working_voices[0]
    else:
        print("\n❌ No working voices found")
        return None

async def update_system_with_working_voice(voice_id: str):
    """Update the fixed system with working voice ID"""
    
    print(f"\n🔧 Updating system with working voice: {voice_id}")
    
    try:
        # Update fixed_murf_client.py
        with open("fixed_murf_client.py", "r") as f:
            content = f.read()
        
        # Replace the default voice ID
        old_default = 'self.default_voice_id = "en-US-sarah"  # Will be updated after fetching real voices'
        new_default = f'self.default_voice_id = "{voice_id}"  # WORKING VOICE ID FOUND'
        
        if old_default in content:
            content = content.replace(old_default, new_default)
        else:
            # Try alternative patterns
            content = content.replace(
                'self.default_voice_id = "en-US-sarah"',
                f'self.default_voice_id = "{voice_id}"'
            )
        
        with open("fixed_murf_client.py", "w") as f:
            f.write(content)
        
        print("✅ Updated fixed_murf_client.py")
        
        # Test the updated system
        print("🧪 Testing updated system...")
        
        # Import and test
        import importlib
        import sys
        
        # Reload the module to get updated code
        if 'fixed_murf_client' in sys.modules:
            importlib.reload(sys.modules['fixed_murf_client'])
        
        from fixed_murf_client import FixedMurfAPIClient, FixedVoiceService
        
        client = FixedMurfAPIClient(api_key)
        service = FixedVoiceService(client)
        
        test_result = await service.text_to_speech("Final system test - voice should work now!")
        
        if test_result["success"]:
            print("🎉 SYSTEM UPDATE SUCCESSFUL!")
            print(f"   Audio file: {test_result['audio_path']}")
            print(f"   Working voice: {voice_id}")
            return True
        else:
            print(f"❌ System test failed: {test_result['error']}")
            return False
    
    except Exception as e:
        print(f"❌ Update failed: {e}")
        return False

async def main():
    """Main execution"""
    
    try:
        # Find working voice
        working_voice = await find_working_voice()
        
        if working_voice:
            # Update system
            success = await update_system_with_working_voice(working_voice)
            
            if success:
                print("\n🎉 VOICE SYSTEM COMPLETELY FIXED!")
                print("=" * 60)
                print(f"✅ Working Voice ID: {working_voice}")
                print("✅ System Updated Successfully")
                print("✅ Voice Generation Tested")
                
                print(f"\n🚀 FINAL STEPS:")
                print(f"1. Restart your server: python main.py")
                print(f"2. Voice service should now show ✅ in logs")
                print(f"3. Test at: http://localhost:8000/api/voice/test")
                print(f"4. Check health: http://localhost:8000/health")
                
                # Show environment update
                print(f"\n📝 Optional: Update your .env file:")
                print(f"DEFAULT_VOICE_ID={working_voice}")
            else:
                print(f"⚠️ Found working voice but system update failed")
                print(f"📝 Manual fix: Edit fixed_murf_client.py line 31")
                print(f"   Change to: self.default_voice_id = \"{working_voice}\"")
        else:
            print("\n❌ Could not find any working voice")
            print("📝 Troubleshooting:")
            print("   1. Verify your Murf API key at https://murf.ai")
            print("   2. Check if your account has TTS API access")
            print("   3. Contact Murf support for voice list")
    
    except Exception as e:
        print(f"❌ Process failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    api_key = os.getenv('MURF_API_KEY', 'ap2_efed6cf1-51d4-4390-989b-f2c4d112dc61')
    print(f"Using API key: {api_key[:15]}...")
    asyncio.run(main())