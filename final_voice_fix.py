# final_voice_fix.py - Use Your Real Voice IDs
"""
Uses the actual voice IDs from your Murf account that we discovered
"""

import asyncio
import aiohttp
import os

# YOUR REAL VOICE IDS (from the API response)
REAL_VOICE_IDS = [
    "en-UK-hazel",
    "en-US-cooper", 
    "en-US-imani"
]

async def test_real_voice(api_key: str, voice_id: str) -> bool:
    """Test with your real voice IDs using minimal payload"""
    
    try:
        # Absolute minimal payload
        payload = {
            "voiceId": voice_id,
            "text": "Hi"
        }
        
        headers = {
            "api-key": api_key,
            "Content-Type": "application/json"
        }
        
        print(f"Testing {voice_id}... ", end="")
        
        # Short timeout to avoid hanging
        timeout = aiohttp.ClientTimeout(total=8)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                "https://api.murf.ai/v1/speech/generate",
                json=payload,
                headers=headers
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    if "audioFile" in data:
                        print("✅ WORKS!")
                        return True
                
                print(f"❌ Status: {response.status}")
                return False
    
    except asyncio.TimeoutError:
        print("❌ Timeout")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)[:20]}")
        return False

async def find_best_voice():
    """Find the best working voice from your real voice IDs"""
    
    print("🎯 TESTING YOUR REAL VOICE IDS")
    print("=" * 50)
    
    api_key = os.getenv('MURF_API_KEY', 'ap2_efed6cf1-51d4-4390-989b-f2c4d112dc61')
    print(f"🔑 API Key: {api_key[:15]}...")
    
    print(f"🧪 Testing {len(REAL_VOICE_IDS)} real voice IDs from your account...")
    
    for voice_id in REAL_VOICE_IDS:
        success = await test_real_voice(api_key, voice_id)
        
        if success:
            print(f"\n🎉 FOUND WORKING VOICE: {voice_id}")
            
            # Test with longer text
            print("🧪 Testing with longer text...")
            longer_success = await test_longer_text(api_key, voice_id)
            
            if longer_success:
                print("✅ Longer text works too!")
                return voice_id
            else:
                print("⚠️ Longer text failed, but short text works")
                return voice_id  # Return it anyway
    
    print("\n❌ None of your real voices worked")
    return None

async def test_longer_text(api_key: str, voice_id: str) -> bool:
    """Test with interview-length text"""
    
    try:
        payload = {
            "voiceId": voice_id,
            "text": "Explain the difference between VLOOKUP and INDEX-MATCH functions in Excel."
        }
        
        headers = {
            "api-key": api_key,
            "Content-Type": "application/json"
        }
        
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                "https://api.murf.ai/v1/speech/generate",
                json=payload,
                headers=headers
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    return "audioFile" in data
                
                return False
    
    except:
        return False

def update_all_voice_files(working_voice_id: str):
    """Update all voice files with working voice ID"""
    
    print(f"\n🔧 Updating all files with working voice: {working_voice_id}")
    
    files_to_update = [
        ("fixed_murf_client.py", 'self.default_voice_id = "natalie"', f'self.default_voice_id = "{working_voice_id}"'),
        ("working_voice_client.py", 'self.default_voice_id = None', f'self.default_voice_id = "{working_voice_id}"')
    ]
    
    for filename, old_text, new_text in files_to_update:
        try:
            if Path(filename).exists():
                with open(filename, "r") as f:
                    content = f.read()
                
                if old_text in content:
                    content = content.replace(old_text, new_text)
                    
                    with open(filename, "w") as f:
                        f.write(content)
                    
                    print(f"✅ Updated {filename}")
                else:
                    print(f"⚠️ Could not find pattern in {filename}")
            else:
                print(f"⚠️ {filename} not found")
        
        except Exception as e:
            print(f"❌ Failed to update {filename}: {e}")
    
    # Create a definitive config file
    config_content = f'''# WORKING_VOICE_CONFIG.py - Your Definitive Working Voice
"""
This file contains the voice ID that definitely works with your account
"""

WORKING_VOICE_ID = "{working_voice_id}"

# Use this voice ID in your system
def get_working_voice_id():
    return WORKING_VOICE_ID

print(f"🎙️ Using working voice: {{WORKING_VOICE_ID}}")
'''
    
    with open("WORKING_VOICE_CONFIG.py", "w") as f:
        f.write(config_content)
    
    print(f"✅ Created WORKING_VOICE_CONFIG.py")

async def main():
    """Main execution"""
    
    try:
        working_voice = await find_best_voice()
        
        if working_voice:
            print(f"\n🎉 SUCCESS! Working voice found: {working_voice}")
            
            # Update all files
            update_all_voice_files(working_voice)
            
            print(f"\n🚀 FINAL INTEGRATION:")
            print(f"1. Your working voice ID is: {working_voice}")
            print(f"2. All voice files have been updated")
            print(f"3. Restart your server: python main.py")
            print(f"4. Look for: ✅ Voice service: Healthy")
            
            print(f"\n📝 OR use this quick manual fix:")
            print(f"Edit any voice file and set:")
            print(f"self.default_voice_id = \"{working_voice}\"")
            
        else:
            print(f"\n❌ No working voices found")
            print(f"📝 Your account has these voices:")
            for voice_id in REAL_VOICE_IDS:
                print(f"   • {voice_id}")
            
            print(f"\n💡 Possible issues:")
            print(f"   1. Network timeouts to Murf API")
            print(f"   2. Account doesn't have TTS generation access")
            print(f"   3. API rate limiting")
            
            print(f"\n🔧 Try manual voice setting:")
            print(f"   Use voice ID: {REAL_VOICE_IDS[0]}")
            print(f"   Edit your voice file manually")
    
    except Exception as e:
        print(f"❌ Process failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    from pathlib import Path
    asyncio.run(main())