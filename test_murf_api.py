# test_murf_api.py - Test the Murf API Fix
"""
Quick test script to verify the Murf API fix is working
Run this first to confirm the fix before updating main.py
"""

import asyncio
import aiohttp

async def test_murf_api_direct():
    """Test Murf API directly with fixed headers"""
    
    print("🧪 TESTING MURF API WITH FIXED HEADERS")
    print("=" * 50)
    
    api_key = "your_murf_key_here"
    
    payload = {
        "voiceId": "en-US-sarah",
        "text": "Hello! This is a test of the fixed Murf API integration.",
        "rate": "0",
        "pitch": "0",
        "volume": "0",
        "audioFormat": "MP3",
        "sampleRate": 22050,
        "bitRate": 128
    }
    
    # FIXED HEADERS
    headers = {
        "api-key": api_key,  # This is the correct header!
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    print("📡 Making request to Murf API...")
    print(f"   API Key: {api_key[:10]}...")
    print(f"   Headers: api-key (instead of Authorization: Bearer)")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.murf.ai/v1/speech/generate",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                print(f"\n📊 Response Status: {response.status}")
                response_text = await response.text()
                print(f"📄 Response: {response_text[:200]}...")
                
                if response.status == 200:
                    print("🎉 SUCCESS! Murf API is working with fixed headers!")
                    
                    try:
                        response_data = await response.json() if response_text else {}
                        if "audioFile" in response_data:
                            print(f"🎵 Audio URL received: {response_data['audioFile'][:50]}...")
                            return True
                        else:
                            print("⚠️ Response successful but no audio file URL")
                            return False
                    except:
                        print("⚠️ Response successful but couldn't parse JSON")
                        return True
                
                elif response.status == 400:
                    if "Missing 'api-key'" in response_text:
                        print("❌ Still getting 'Missing api-key' error")
                        print("💡 The API might need a different header format")
                        return False
                    else:
                        print(f"❌ Bad request: {response_text}")
                        return False
                
                elif response.status == 401:
                    print("❌ Unauthorized - API key might be invalid")
                    return False
                
                elif response.status == 429:
                    print("⚠️ Rate limited - try again in a moment")
                    return False
                
                else:
                    print(f"❌ Unexpected status: {response.status}")
                    return False
    
    except asyncio.TimeoutError:
        print("❌ Request timed out")
        return False
    
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

async def test_with_fixed_client():
    """Test with the fixed client class"""
    
    print("\n🔧 TESTING WITH FIXED CLIENT CLASS")
    print("=" * 50)
    
    try:
        from fixed_murf_client import FixedMurfAPIClient, FixedVoiceService
        
        api_key = "your_murf_key_here"
        
        # Create fixed client
        murf_client = FixedMurfAPIClient(api_key)
        voice_service = FixedVoiceService(murf_client)
        
        print(f"🎛️ Client Available: {murf_client.available}")
        print(f"🎙️ Service Available: {voice_service.available}")
        
        if voice_service.available:
            print("\n🎵 Testing text-to-speech...")
            result = await voice_service.text_to_speech(
                "Hello! This is a comprehensive test of the fixed voice system."
            )
            
            if result["success"]:
                print("🎉 SUCCESS! Fixed voice client is working!")
                print(f"   Audio Path: {result['audio_path']}")
                print(f"   Voice ID: {result['voice_id']}")
                print(f"   Text Length: {result['text_length']}")
                
                # Check if file exists
                from pathlib import Path
                if Path(result['audio_path']).exists():
                    file_size = Path(result['audio_path']).stat().st_size
                    print(f"   File Size: {file_size} bytes")
                    print("✅ Audio file created successfully!")
                else:
                    print("⚠️ Audio file not found on disk")
                
                return True
            else:
                print(f"❌ TTS failed: {result['error']}")
                return False
        else:
            print("❌ Voice service not available")
            return False
    
    except ImportError:
        print("❌ Could not import fixed_murf_client")
        print("💡 Make sure fixed_murf_client.py is in the same directory")
        return False
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

async def main():
    """Main test function"""
    
    print("🔍 MURF API FIX VERIFICATION")
    print("=" * 60)
    
    # Test 1: Direct API test
    direct_success = await test_murf_api_direct()
    
    # Test 2: Fixed client test
    client_success = await test_with_fixed_client()
    
    # Results
    print("\n📋 TEST RESULTS")
    print("=" * 30)
    print(f"Direct API Test: {'✅ PASS' if direct_success else '❌ FAIL'}")
    print(f"Fixed Client Test: {'✅ PASS' if client_success else '❌ FAIL'}")
    
    if direct_success and client_success:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ The voice system fix is working correctly")
        print("\n📋 Next Steps:")
        print("1. Run: python voice_system_replacer.py")
        print("2. Restart your server: python main.py")
        print("3. Check voice status at: http://localhost:8000/health")
    
    elif direct_success:
        print("\n⚠️ Direct API works but fixed client has issues")
        print("💡 Check if fixed_murf_client.py is properly created")
    
    else:
        print("\n❌ API test failed")
        print("💡 Possible issues:")
        print("   - API key might be invalid")
        print("   - Network connectivity issues")
        print("   - Murf API might have changed")

if __name__ == "__main__":
    print("🧪 Murf API Fix Test")
    print("This will verify if the header fix resolves the voice system issue.")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Test cancelled")
    except Exception as e:
        print(f"\n❌ Test script failed: {e}")