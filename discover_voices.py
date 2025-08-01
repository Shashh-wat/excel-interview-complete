# discover_voices.py - Find Correct Murf Voice IDs
"""
This script discovers the actual voice IDs available in your Murf account
and tests TTS with the correct voice ID.
"""

import asyncio
import os
from fixed_murf_client import FixedMurfAPIClient

async def discover_and_test_voices():
    """Discover available voices and test TTS"""
    
    print("🔍 MURF VOICE DISCOVERY")
    print("=" * 50)
    
    # Get API key
    api_key = os.getenv('MURF_API_KEY', 'your_murf_key_here')
    print(f"🔑 Using API key: {api_key[:15]}...")
    
    # Create client
    murf_client = FixedMurfAPIClient(api_key)
    
    if not murf_client.available:
        print("❌ Murf client not available")
        return False
    
    # Step 1: Get available voices
    print("\n1️⃣ Fetching available voices...")
    voices_result = await murf_client.get_available_voices()
    
    if voices_result["success"]:
        voices = voices_result["voices"]
        print(f"✅ Found {len(voices)} available voices:")
        
        english_voices = []
        for i, voice in enumerate(voices[:10]):  # Show first 10
            voice_id = voice.get('voice_id', voice.get('id', 'unknown'))
            voice_name = voice.get('voice_name', voice.get('name', 'Unknown'))
            language = voice.get('language', 'Unknown')
            gender = voice.get('gender', 'Unknown')
            
            print(f"   {i+1}. ID: {voice_id}")
            print(f"      Name: {voice_name}")
            print(f"      Language: {language}")
            print(f"      Gender: {gender}")
            print()
            
            # Collect English voices
            if 'en' in language.lower() or 'english' in language.lower():
                english_voices.append(voice_id)
        
        if english_voices:
            print(f"🎯 English voices found: {english_voices[:3]}")
            
            # Step 2: Test with first English voice
            test_voice_id = english_voices[0]
            print(f"\n2️⃣ Testing TTS with voice: {test_voice_id}")
            
            test_result = await murf_client.text_to_speech(
                "Hello! This is a test of the Murf voice system with the correct voice ID.",
                test_voice_id
            )
            
            if test_result["success"]:
                print("🎉 SUCCESS! TTS is now working!")
                print(f"   Audio file: {test_result['audio_path']}")
                print(f"   Audio URL: {test_result['audio_url']}")
                
                # Update your .env file suggestion
                print(f"\n📝 UPDATE YOUR .env FILE:")
                print(f"DEFAULT_VOICE_ID={test_voice_id}")
                
                return True, test_voice_id
            else:
                print(f"❌ TTS still failed: {test_result['error']}")
                
                # Try another voice
                if len(english_voices) > 1:
                    print(f"\n🔄 Trying backup voice: {english_voices[1]}")
                    backup_result = await murf_client.text_to_speech(
                        "Testing backup voice",
                        english_voices[1]
                    )
                    
                    if backup_result["success"]:
                        print("🎉 SUCCESS with backup voice!")
                        print(f"📝 USE THIS VOICE ID: {english_voices[1]}")
                        return True, english_voices[1]
        else:
            print("❌ No English voices found")
    
    else:
        print(f"❌ Failed to get voices: {voices_result['error']}")
    
    return False, None

async def update_voice_config(working_voice_id: str):
    """Update configuration with working voice ID"""
    
    print(f"\n🔧 Updating configuration with working voice ID: {working_voice_id}")
    
    # Update the fixed client default
    config_update = f'''
# Add this to your .env file or update voice_fix_integration.py:
DEFAULT_VOICE_ID = "{working_voice_id}"

# Or update fixed_murf_client.py line 31:
self.default_voice_id = "{working_voice_id}"
'''
    
    print(config_update)
    
    # Try to update the integration file
    try:
        with open("voice_fix_integration.py", "r") as f:
            content = f.read()
        
        # Add voice ID configuration
        addition = f'''
# WORKING VOICE ID DISCOVERED
WORKING_VOICE_ID = "{working_voice_id}"

def get_working_voice_id():
    return WORKING_VOICE_ID
'''
        
        content = content + addition
        
        with open("voice_fix_integration.py", "w") as f:
            f.write(content)
        
        print("✅ Updated voice_fix_integration.py with working voice ID")
        
    except Exception as e:
        print(f"⚠️ Could not auto-update config: {e}")

async def main():
    """Main discovery process"""
    
    try:
        success, working_voice_id = await discover_and_test_voices()
        
        if success and working_voice_id:
            await update_voice_config(working_voice_id)
            
            print("\n🎉 VOICE SYSTEM FULLY FIXED!")
            print("=" * 50)
            print("📋 FINAL STEPS:")
            print(f"1. Your working voice ID is: {working_voice_id}")
            print("2. Restart your server: python main.py")
            print("3. Test at: http://localhost:8000/api/voice/test")
            print("4. The voice system should now show ✅ in logs")
            
            # Test one more time to confirm
            print(f"\n🧪 Final confirmation test...")
            api_key = os.getenv('MURF_API_KEY', 'your_murf_key_here')
            client = FixedMurfAPIClient(api_key)
            client.default_voice_id = working_voice_id  # Use discovered voice
            
            final_test = await client.text_to_speech(
                "Final test - voice system is now working!",
                working_voice_id
            )
            
            if final_test["success"]:
                print("🎉 FINAL TEST PASSED! System is ready!")
            else:
                print(f"⚠️ Final test issue: {final_test['error']}")
        
        else:
            print("\n❌ Voice discovery failed")
            print("📝 Troubleshooting:")
            print("   1. Check your Murf API key is valid")
            print("   2. Verify your Murf account has TTS access")
            print("   3. Check internet connectivity")
            print("   4. Visit https://murf.ai/api/docs/voices-styles/voice-library")
    
    except Exception as e:
        print(f"❌ Discovery failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())