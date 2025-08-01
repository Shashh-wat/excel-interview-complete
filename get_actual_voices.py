# get_actual_voices.py - Get Your Real Murf Voices
"""
This script gets the ACTUAL voices available in YOUR Murf account
and tests them to find working ones.
"""

import asyncio
import aiohttp
import os
import json

async def get_real_murf_voices():
    """Get actual voices from your Murf account"""
    
    print("🎙️ GETTING YOUR ACTUAL MURF VOICES")
    print("=" * 60)
    
    api_key = os.getenv('MURF_API_KEY', 'ap2_efed6cf1-51d4-4390-989b-f2c4d112dc61')
    print(f"🔑 API Key: {api_key[:15]}...")
    
    try:
        headers = {
            "api-key": api_key,
            "Accept": "application/json"
        }
        
        print("📞 Calling Murf API to get your voices...")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.murf.ai/v1/speech/voices",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                print(f"📞 API Response: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Success! Got voices data")
                    
                    # Print the raw response to see the structure
                    print(f"\n📋 Raw API Response Structure:")
                    if isinstance(data, dict):
                        print(f"Type: Dictionary with keys: {list(data.keys())}")
                        voices = data.get('voices', data.get('data', []))
                    elif isinstance(data, list):
                        print(f"Type: List with {len(data)} items")
                        voices = data
                    else:
                        print(f"Type: {type(data)}")
                        voices = []
                    
                    print(f"📊 Total voices found: {len(voices)}")
                    
                    if voices:
                        print(f"\n🎭 YOUR AVAILABLE VOICES:")
                        print("=" * 40)
                        
                        working_voices = []
                        
                        for i, voice in enumerate(voices):
                            print(f"\nVoice {i+1}:")
                            print(f"Raw voice data: {voice}")
                            
                            # Handle different voice object formats
                            voice_id = (
                                voice.get('voice_id') or 
                                voice.get('id') or 
                                voice.get('voiceId') or 
                                voice.get('name') or
                                f"voice_{i}"
                            )
                            
                            voice_name = (
                                voice.get('voice_name') or 
                                voice.get('name') or 
                                voice.get('displayName') or
                                voice_id
                            )
                            
                            language = (
                                voice.get('language') or 
                                voice.get('locale') or 
                                voice.get('lang') or
                                'Unknown'
                            )
                            
                            gender = (
                                voice.get('gender') or 
                                voice.get('sex') or
                                'Unknown'
                            )
                            
                            print(f"   ID: {voice_id}")
                            print(f"   Name: {voice_name}")
                            print(f"   Language: {language}")
                            print(f"   Gender: {gender}")
                            
                            # Test this voice immediately
                            print(f"   Testing... ", end="")
                            test_result = await test_voice_directly(api_key, voice_id)
                            if test_result:
                                working_voices.append(voice_id)
                                print(f"✅ WORKS!")
                            else:
                                print(f"❌ Failed")
                        
                        if working_voices:
                            print(f"\n🎉 WORKING VOICES: {working_voices}")
                            return working_voices[0], voices
                        else:
                            print(f"\n❌ None of the voices worked")
                            return None, voices
                    else:
                        print("❌ No voices in response")
                        return None, []
                
                else:
                    error_text = await response.text()
                    print(f"❌ API Error {response.status}:")
                    print(f"   {error_text}")
                    
                    if response.status == 401:
                        print("🔑 API key issue - check your Murf account")
                    elif response.status == 403:
                        print("🚫 Account access issue - check TTS permissions")
                    
                    return None, []
    
    except Exception as e:
        print(f"❌ Error getting voices: {e}")
        return None, []

async def test_voice_directly(api_key: str, voice_id: str) -> bool:
    """Test voice directly with minimal payload"""
    
    try:
        # Minimal test payload
        payload = {
            "voiceId": voice_id,
            "text": "Hi",
            "audioFormat": "MP3"
        }
        
        headers = {
            "api-key": api_key,
            "Content-Type": "application/json"
        }
        
        print(f"   Testing {voice_id}... ", end="")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.murf.ai/v1/speech/generate",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    if "audioFile" in data:
                        print("✅ WORKS!")
                        return True
                    else:
                        print("❌ No audio file")
                        return False
                else:
                    error = await response.text()
                    print(f"❌ {response.status}")
                    return False
    
    except Exception as e:
        print(f"❌ Error: {str(e)[:30]}")
        return False

async def create_working_voice_file(working_voice_id: str):
    """Create a file with the working voice ID"""
    
    working_config = f'''# working_voice_config.py - Your Working Voice Configuration
"""
This file contains the voice ID that actually works with your Murf account
"""

WORKING_VOICE_ID = "{working_voice_id}"

def get_working_voice():
    return WORKING_VOICE_ID

def create_working_voice_system(api_key: str):
    """Create voice system with guaranteed working voice"""
    
    from working_voice_client import WorkingMurfClient, WorkingVoiceService
    
    client = WorkingMurfClient(api_key)
    client.default_voice_id = WORKING_VOICE_ID  # Force working voice
    
    service = WorkingVoiceService(client)
    
    print(f"🎙️ Created voice system with working voice: {{WORKING_VOICE_ID}}")
    
    return client, service

# For main.py integration
MurfAPIClient = WorkingMurfClient
VoiceService = WorkingVoiceService

def initialize_working_voice_system(api_key: str):
    """Drop-in replacement for broken voice system"""
    return create_working_voice_system(api_key)
'''
    
    with open("working_voice_config.py", "w") as f:
        f.write(working_config)
    
    print(f"✅ Created working_voice_config.py with voice: {working_voice_id}")

async def main():
    """Main execution"""
    
    try:
        working_voice, all_voices = await get_real_murf_voices()
        
        if working_voice:
            print(f"\n🎉 FOUND WORKING VOICE: {working_voice}")
            
            # Create config file
            await create_working_voice_file(working_voice)
            
            # Test the working voice one more time
            print(f"\n🧪 Final test with {working_voice}...")
            final_test = await test_voice_directly(
                os.getenv('MURF_API_KEY', 'ap2_efed6cf1-51d4-4390-989b-f2c4d112dc61'),
                working_voice
            )
            
            if final_test:
                print(f"✅ CONFIRMED WORKING!")
                
                print(f"\n🚀 READY TO INTEGRATE:")
                print(f"   Working Voice: {working_voice}")
                print(f"   1. Update main.py to use: {working_voice}")
                print(f"   2. Or use working_voice_config.py")
                print(f"   3. Restart server: python main.py")
                
                # Show simple integration
                print(f"\n📝 SIMPLE FIX FOR MAIN.PY:")
                print(f"Add this line in your voice initialization:")
                print(f"murf_client.default_voice_id = '{working_voice}'")
                
            else:
                print(f"❌ Final test failed")
        
        else:
            print(f"\n❌ No working voices found")
            
            if all_voices:
                print(f"📋 Your account has {len(all_voices)} voices but none worked")
                print(f"🔍 First voice details:")
                first_voice = all_voices[0]
                for key, value in first_voice.items():
                    print(f"   {key}: {value}")
                    
                print(f"\n💡 Try contacting Murf support about API access")
            else:
                print(f"📋 Could not get voices from API")
                print(f"💡 Check your Murf account and API key")
    
    except Exception as e:
        print(f"❌ Process failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())