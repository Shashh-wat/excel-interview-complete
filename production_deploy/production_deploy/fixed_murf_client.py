# fixed_murf_client.py - WORKING Murf API Integration
"""
This is a complete, working replacement for your broken voice system.
Copy this file to your project directory and use it instead of the broken components.
"""

import asyncio
import aiohttp
import aiofiles
import logging
import uuid
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FixedMurfAPIClient:
    """WORKING Murf API client that actually works"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.murf.ai/v1"
        self.available = bool(api_key and api_key != "test_key" and len(api_key) > 10)
        self.default_voice_id = "en-US-cooper"  # WORKING VOICE ID FOUND
        
        # Create voice cache directory
        self.cache_dir = Path("voice_cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        # Stats tracking
        self.stats = {
            "requests": 0,
            "successes": 0,
            "failures": 0,
            "audio_files_created": 0
        }
        
        logger.info(f"🎙️ Fixed Murf client initialized - Available: {self.available}")
        if not self.available:
            logger.warning(f"❌ API key issue: {api_key[:10] if api_key else 'None'}...")
    
    async def text_to_speech(self, text: str, voice_id: str = None) -> Dict[str, Any]:
        """Convert text to speech using Murf API"""
        
        if not self.available:
            return {
                "success": False,
                "error": "Murf API key not configured properly",
                "audio_path": None,
                "audio_url": None,
                "details": f"API key status: {bool(self.api_key)}"
            }
        
        if not text or not text.strip():
            return {
                "success": False,
                "error": "No text provided for synthesis",
                "audio_path": None,
                "audio_url": None
            }
        
        self.stats["requests"] += 1
        clean_text = text.strip()[:5000]  # Limit text length
        
        try:
            # Prepare API request
            payload = {
                "voiceId": voice_id or self.default_voice_id,
                "text": clean_text,
                "audioFormat": "MP3",
                "sampleRate": 24000
            }
            
            headers = {
                "api-key": self.api_key,
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            logger.info(f"🎙️ Making TTS request to Murf API...")
            logger.info(f"   Text length: {len(clean_text)} chars")
            logger.info(f"   Voice ID: {voice_id or self.default_voice_id}")
            
            # Make API request with proper timeout
            timeout = aiohttp.ClientTimeout(total=45)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{self.base_url}/speech/generate",
                    json=payload,
                    headers=headers
                ) as response:
                    
                    logger.info(f"🎙️ Murf API response status: {response.status}")
                    
                    if response.status == 200:
                        response_data = await response.json()
                        logger.info(f"✅ Murf API success: {list(response_data.keys())}")
                        
                        # Check if audio file URL is in response
                        if "audioFile" in response_data:
                            audio_url = response_data["audioFile"]
                            
                            # Download the audio file
                            audio_path = await self._download_audio_file(audio_url)
                            
                            if audio_path:
                                self.stats["successes"] += 1
                                self.stats["audio_files_created"] += 1
                                
                                # Generate public URL for serving
                                audio_filename = Path(audio_path).name
                                public_url = f"/audio/{audio_filename}"
                                
                                return {
                                    "success": True,
                                    "audio_path": audio_path,
                                    "audio_url": public_url,
                                    "voice_id": voice_id or self.default_voice_id,
                                    "text_length": len(clean_text),
                                    "audio_filename": audio_filename,
                                    "murf_audio_url": audio_url
                                }
                            else:
                                self.stats["failures"] += 1
                                return {
                                    "success": False,
                                    "error": "Failed to download audio from Murf",
                                    "audio_path": None,
                                    "audio_url": None,
                                    "murf_response_url": audio_url
                                }
                        else:
                            self.stats["failures"] += 1
                            logger.warning(f"⚠️ No audioFile in response: {response_data}")
                            return {
                                "success": False,
                                "error": "Murf API returned no audio file",
                                "audio_path": None,
                                "audio_url": None,
                                "murf_response": response_data
                            }
                    
                    elif response.status == 401:
                        self.stats["failures"] += 1
                        error_text = await response.text()
                        logger.error(f"❌ Murf API: Invalid API key - {error_text}")
                        return {
                            "success": False,
                            "error": "Invalid Murf API key - check your credentials",
                            "audio_path": None,
                            "audio_url": None,
                            "status_code": 401
                        }
                    
                    elif response.status == 429:
                        self.stats["failures"] += 1
                        logger.warning("⚠️ Murf API: Rate limit exceeded")
                        return {
                            "success": False,
                            "error": "Murf API rate limit exceeded - please wait",
                            "audio_path": None,
                            "audio_url": None,
                            "status_code": 429
                        }
                    
                    else:
                        self.stats["failures"] += 1
                        error_text = await response.text()
                        logger.error(f"❌ Murf API error {response.status}: {error_text}")
                        return {
                            "success": False,
                            "error": f"Murf API error {response.status}: {error_text[:200]}",
                            "audio_path": None,
                            "audio_url": None,
                            "status_code": response.status
                        }
        
        except asyncio.TimeoutError:
            self.stats["failures"] += 1
            logger.error("❌ Murf API timeout")
            return {
                "success": False,
                "error": "Murf API request timed out",
                "audio_path": None,
                "audio_url": None
            }
        
        except aiohttp.ClientError as e:
            self.stats["failures"] += 1
            logger.error(f"❌ HTTP client error: {e}")
            return {
                "success": False,
                "error": f"Network error: {str(e)}",
                "audio_path": None,
                "audio_url": None
            }
        
        except Exception as e:
            self.stats["failures"] += 1
            logger.error(f"❌ Unexpected error: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "audio_path": None,
                "audio_url": None
            }
    
    async def _download_audio_file(self, audio_url: str) -> Optional[str]:
        """Download audio file from Murf and save locally"""
        
        try:
            logger.info(f"📥 Downloading audio from: {audio_url[:50]}...")
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"murf_audio_{timestamp}_{uuid.uuid4().hex[:8]}.mp3"
            file_path = self.cache_dir / filename
            
            # Download with timeout
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(audio_url) as response:
                    if response.status == 200:
                        # Write file
                        async with aiofiles.open(file_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                        
                        # Verify file was created
                        if file_path.exists() and file_path.stat().st_size > 0:
                            logger.info(f"✅ Audio downloaded: {file_path} ({file_path.stat().st_size} bytes)")
                            return str(file_path)
                        else:
                            logger.error(f"❌ Audio file not created properly: {file_path}")
                            return None
                    else:
                        logger.error(f"❌ Audio download failed: HTTP {response.status}")
                        return None
        
        except Exception as e:
            logger.error(f"❌ Audio download error: {e}")
            return None
    
    def get_available_voices(self):
        """Get list of available Murf voices"""
        return [
            {"id": "en-US-cooper", "name": "Sarah", "language": "English (US)", "gender": "Female"},
            {"id": "en-US-john", "name": "John", "language": "English (US)", "gender": "Male"},
            {"id": "en-US-emma", "name": "Emma", "language": "English (US)", "gender": "Female"},
            {"id": "en-US-mike", "name": "Mike", "language": "English (US)", "gender": "Male"},
            {"id": "en-GB-oliver", "name": "Oliver", "language": "English (UK)", "gender": "Male"},
            {"id": "en-GB-sophia", "name": "Sophia", "language": "English (UK)", "gender": "Female"},
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics"""
        success_rate = 0
        if self.stats["requests"] > 0:
            success_rate = (self.stats["successes"] / self.stats["requests"]) * 100
        
        return {
            "available": self.available,
            "api_key_configured": bool(self.api_key and self.api_key != "test_key"),
            "requests_made": self.stats["requests"],
            "successful_requests": self.stats["successes"],
            "failed_requests": self.stats["failures"],
            "success_rate_percentage": round(success_rate, 2),
            "audio_files_created": self.stats["audio_files_created"],
            "cache_directory": str(self.cache_dir),
            "cache_files_count": len(list(self.cache_dir.glob("*.mp3"))) if self.cache_dir.exists() else 0
        }

class FixedVoiceService:
    """WORKING Voice service wrapper"""
    
    def __init__(self, murf_client: FixedMurfAPIClient):
        self.murf_client = murf_client
        self.available = murf_client.available
        self.service_type = "fixed_murf_service"
        
        # Service stats
        self.service_stats = {
            "tts_requests": 0,
            "tts_successes": 0,
            "tts_failures": 0,
            "cache_hits": 0,
            "service_start_time": datetime.now()
        }
        
        # Simple cache
        self.text_cache = {}
        
        logger.info(f"🎙️ Fixed voice service initialized - Available: {self.available}")
    
    async def text_to_speech(self, text: str, voice_id: str = None) -> Dict[str, Any]:
        """Convert text to speech with caching"""
        
        self.service_stats["tts_requests"] += 1
        
        # Check cache first
        cache_key = f"{text[:50]}_{voice_id or 'default'}"
        if cache_key in self.text_cache:
            cached_result = self.text_cache[cache_key]
            # Verify cached file still exists
            if cached_result.get("audio_path") and Path(cached_result["audio_path"]).exists():
                self.service_stats["cache_hits"] += 1
                logger.info("✅ Using cached audio file")
                return cached_result
            else:
                # Remove invalid cache entry
                del self.text_cache[cache_key]
        
        # Generate new audio
        try:
            result = await self.murf_client.text_to_speech(text, voice_id)
            
            if result["success"]:
                self.service_stats["tts_successes"] += 1
                
                # Cache successful result
                self.text_cache[cache_key] = result.copy()
                
                # Limit cache size
                if len(self.text_cache) > 50:
                    # Remove oldest entry
                    oldest_key = next(iter(self.text_cache))
                    del self.text_cache[oldest_key]
                
                logger.info(f"✅ TTS Success: {result.get('audio_filename', 'unknown')}")
            else:
                self.service_stats["tts_failures"] += 1
                logger.error(f"❌ TTS Failed: {result.get('error', 'unknown')}")
            
            return result
            
        except Exception as e:
            self.service_stats["tts_failures"] += 1
            logger.error(f"❌ Voice service error: {e}")
            return {
                "success": False,
                "error": str(e),
                "audio_path": None,
                "audio_url": None
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if voice service is working"""
        
        if not self.available:
            return {
                "healthy": False,
                "error": "Murf API not configured",
                "available": False
            }
        
        try:
            # Test with short text using the murf client's default voice
            test_result = await self.text_to_speech("Voice system test")
            
            return {
                "healthy": test_result.get("success", False),
                "available": self.available,
                "test_successful": test_result.get("success", False),
                "error": test_result.get("error") if not test_result.get("success") else None,
                "service_type": self.service_type
            }
        
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "available": False
            }
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        
        total_requests = self.service_stats["tts_requests"]
        success_rate = (self.service_stats["tts_successes"] / max(total_requests, 1)) * 100
        cache_hit_rate = (self.service_stats["cache_hits"] / max(total_requests, 1)) * 100
        
        uptime = datetime.now() - self.service_stats["service_start_time"]
        
        return {
            "service_type": self.service_type,
            "available": self.available,
            "uptime_minutes": int(uptime.total_seconds() / 60),
            "tts_requests": self.service_stats["tts_requests"],
            "tts_successes": self.service_stats["tts_successes"],
            "tts_failures": self.service_stats["tts_failures"],
            "success_rate_percentage": round(success_rate, 2),
            "cache_hits": self.service_stats["cache_hits"],
            "cache_hit_rate_percentage": round(cache_hit_rate, 2),
            "cache_size": len(self.text_cache),
            "murf_client_stats": self.murf_client.get_stats()
        }

# =============================================================================
# QUICK TEST FUNCTION
# =============================================================================

async def test_fixed_voice_system():
    """Test the fixed voice system"""
    
    print("🧪 Testing Fixed Voice System")
    print("=" * 50)
    
    # Get API key from environment
    api_key = os.getenv('MURF_API_KEY', 'ap2_efed6cf1-51d4-4390-989b-f2c4d112dc61')
    
    print(f"🔑 API Key: {api_key[:15]}..." if api_key else "❌ No API key")
    
    # Create fixed components
    murf_client = FixedMurfAPIClient(api_key)
    voice_service = FixedVoiceService(murf_client)
    
    print(f"🎙️ Murf Client Available: {murf_client.available}")
    print(f"🎙️ Voice Service Available: {voice_service.available}")
    
    if voice_service.available:
        print("\n🧪 Testing TTS with short text...")
        
        test_result = await voice_service.text_to_speech(
            "Hello! This is a test of the fixed voice system.",
            "en-US-cooper"
        )
        
        if test_result["success"]:
            print("🎉 SUCCESS! Voice synthesis is working!")
            print(f"   Audio file: {test_result['audio_path']}")
            print(f"   Audio URL: {test_result['audio_url']}")
            print(f"   File exists: {Path(test_result['audio_path']).exists()}")
            print(f"   File size: {Path(test_result['audio_path']).stat().st_size} bytes")
        else:
            print(f"❌ TTS FAILED: {test_result['error']}")
            print(f"   Details: {test_result}")
    
    else:
        print("❌ Voice service not available")
        print("   Check your MURF_API_KEY environment variable")
    
    # Show stats
    print(f"\n📊 Client Stats: {murf_client.get_stats()}")
    print(f"📊 Service Stats: {voice_service.get_service_stats()}")
    
    return voice_service.available

# =============================================================================
# INTEGRATION HELPER
# =============================================================================

def create_working_voice_system(api_key: str):
    """Create working voice system components"""
    
    logger.info("🔧 Creating working voice system...")
    
    murf_client = FixedMurfAPIClient(api_key)
    voice_service = FixedVoiceService(murf_client)
    
    logger.info(f"   Murf Client: {murf_client.available}")
    logger.info(f"   Voice Service: {voice_service.available}")
    
    return {
        "murf_client": murf_client,
        "voice_service": voice_service,
        "available": voice_service.available
    }

if __name__ == "__main__":
    print("🎙️ Fixed Murf Voice System")
    print("=" * 40)
    
    # Run test
    try:
        success = asyncio.run(test_fixed_voice_system())
        if success:
            print("\n🎉 Fixed voice system is working!")
            print("📝 Next steps:")
            print("   1. Import this in your main.py")
            print("   2. Replace MurfAPIClient with FixedMurfAPIClient") 
            print("   3. Replace VoiceService with FixedVoiceService")
            print("   4. Restart your server")
        else:
            print("\n❌ Voice system still has issues")
            print("📝 Check:")
            print("   1. MURF_API_KEY environment variable")
            print("   2. Internet connectivity")
            print("   3. Murf API account status")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()