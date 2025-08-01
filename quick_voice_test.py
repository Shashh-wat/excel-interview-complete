# quick_voice_test.py - Find Working Voice ID Fast
"""
This script quickly finds a working voice ID by testing common Murf voice IDs
"""

import asyncio
import aiohttp
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuickVoiceTester:
    """Quick voice ID tester"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.murf.ai/v1"
        self.available = bool(api_key and len(api_key) > 10)
    
    async def get_voices_from_api(self):
        """Get actual voices from Murf API"""
        
        if not self.available:
            return None
        
        try:
            headers = {
                "api-key": self.api_key,
                "Accept": "application/json"
            }
            
            print("🔍 Fetching voices from Murf API...")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/speech/voices",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        error = await response.text()
                        print(f"❌ API Error {response.status}: {error}")
                        return None
        
        except Exception as e:
            print(f"❌ Error getting voices: {e}")
            return None
    
    async def test_voice_id(self, voice_id: str, test_text: str = "Test") -> bool:
        """Test if a voice ID works"""
        
        try:
            payload = {
                "voiceId": voice_id,
                "text": test_text,
                "audioFormat": "MP3"
            }
            
            headers = {
                "api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/speech/generate",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        if "audioFile" in data:
                            return True
                    
                    return False
        
        except Exception as e:
            print(f"   Error testing {voice_id}: {e}")
            return False

async def main():
    """Main voice discovery process"""
    
    print("🎙️ QUICK VOICE ID DISCOVERY")
    print("=" * 50)
    
    # Get API key
    api_key = os.getenv('MURF_API_KEY', 'ap2_efed6cf1-51d4-4390-989b-f2c4d112dc61')
    print(f"🔑 API Key: {api_key[:15]}...")
    
    tester = QuickVoiceTester(api_key)
    
    if not tester.available:
        print("❌ API key not available")
        return
    
    # Step 1: Try to get actual voices
    print("\n1️⃣ Getting available voices...")
    voices_data = await tester.get_voices_from_api()
    
    working_voice_id = None
    
    if voices_data and "voices" in voices_data:
        voices = voices_data["voices"]
        print(f"✅ Found {len(voices)} voices in your account:")
        
        # Show first few voices
        english_voices = []
        for voice in voices[:10]:
            voice_id = voice.get('voice_id', voice.get('id', voice.get('voiceId', 'unknown')))
            voice_name = voice.get('voice_name', voice.get('name', 'Unknown'))
            language = voice.get('language', voice.get('locale', 'Unknown'))
            
            print(f"   • {voice_id} - {voice_name} ({language})")
            
            # Collect English voices
            if any(lang in language.lower() for lang in ['en', 'english']) or any(lang in voice_id.lower() for lang in ['en-', 'english']):
                english_voices.append(voice_id)
        
        # Step 2: Test first English voice
        if english_voices:
            print(f"\n2️⃣ Testing first English voice: {english_voices[0]}")
            
            success = await tester.test_voice_id(english_voices[0], "Hello, this is a test.")
            
            if success:
                working_voice_id = english_voices[0]
                print(f"🎉 SUCCESS! Working voice ID: {working_voice_id}")
            else:
                print(f"❌ First voice failed, trying others...")
                
                # Try other English voices
                for voice_id in english_voices[1:3]:
                    print(f"   Testing: {voice_id}")
                    if await tester.test_voice_id(voice_id, "Test"):
                        working_voice_id = voice_id
                        print(f"🎉 SUCCESS! Working voice ID: {working_voice_id}")
                        break
    
    else:
        print("⚠️ Could not get voices from API, trying common voice IDs...")
        
        # Step 3: Try common voice IDs
        common_voice_ids = [
            "sarah",
            "john", 
            "emma",
            "mike",
            "en_us_sarah",
            "en_us_john",
            "english_sarah",
            "english_john"
        ]
        
        print("🧪 Testing common voice IDs...")
        for voice_id in common_voice_ids:
            print(f"   Testing: {voice_id}")
            
            if await tester.test_voice_id(voice_id, "Quick test"):
                working_voice_id = voice_id
                print(f"🎉 SUCCESS! Working voice ID: {working_voice_id}")
                break
    
    # Final result
    if working_voice_id:
        print(f"\n🎯 WORKING VOICE ID FOUND: {working_voice_id}")
        print("=" * 50)
        
        # Update fixed_murf_client.py
        try:
            with open("fixed_murf_client.py", "r") as f:
                content = f.read()
            
            # Replace default voice ID
            old_line = 'self.default_voice_id = "en-US-sarah"  # Will be updated after fetching real voices'
            new_line = f'self.default_voice_id = "{working_voice_id}"  # WORKING VOICE ID'
            
            content = content.replace(old_line, new_line)
            
            with open("fixed_murf_client.py", "w") as f:
                f.write(content)
            
            print(f"✅ Updated fixed_murf_client.py with working voice ID")
            
            # Test the updated system
            print(f"\n🧪 Final test with updated system...")
            from fixed_murf_client import FixedMurfAPIClient, FixedVoiceService
            
            client = FixedMurfAPIClient(api_key)
            service = FixedVoiceService(client)
            
            final_result = await service.text_to_speech("Final test - voice system is working!")
            
            if final_result["success"]:
                print("🎉 FINAL TEST PASSED! Your voice system is now fully working!")
                print(f"   Audio file: {final_result['audio_path']}")
                
                print(f"\n🚀 READY TO USE!")
                print(f"   Working Voice ID: {working_voice_id}")
                print(f"   Restart your server: python main.py")
                print(f"   The voice service should now show ✅ in logs")
            else:
                print(f"⚠️ Final test failed: {final_result['error']}")
        
        except Exception as e:
            print(f"⚠️ Could not auto-update files: {e}")
            print(f"📝 MANUAL UPDATE NEEDED:")
            print(f"   1. Edit fixed_murf_client.py")
            print(f"   2. Change line 31 to: self.default_voice_id = \"{working_voice_id}\"")
    
    else:
        print("\n❌ NO WORKING VOICE ID FOUND")
        print("📝 Possible issues:")
        print("   1. Invalid Murf API key")
        print("   2. Murf account doesn't have TTS access")
        print("   3. Network connectivity issues")
        print("   4. Murf API changes")
        print("\n💡 Solutions:")
        print("   1. Check your Murf account at https://murf.ai")
        print("   2. Verify API key in your account dashboard")
        print("   3. Check API documentation: https://murf.ai/api/docs")

if __name__ == "__main__":
    asyncio.run(main())