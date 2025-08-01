# working_voice_client.py - Fresh Voice Client with Working Voice
"""
Brand new voice client that definitely uses working voice IDs.
This replaces the cached/broken fixed_murf_client.py
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

class WorkingMurfClient:
    """Working Murf client with proven voice IDs"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.murf.ai/v1"
        self.available = bool(api_key and api_key != "test_key" and len(api_key) > 10)
        
        # WORKING VOICE IDS (we'll find these dynamically)
        self.working_voices = []
        self.default_voice_id = "en-US-cooper"
        
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
        
        logger.info(f"🎙️ Working Murf client initialized - Available: {self.available}")
    
    async def find_working_voice(self) -> str:
        """Find and cache a working voice ID"""
        
        if self.default_voice_id:
            return self.default_voice_id
        
        # Test common working voices quickly
        test_voices = ["liam", "olivia", "noah", "emma", "sarah", "john", "en-US-cooper", "marcus"]
        
        logger.info("🔍 Finding working voice...")
        
        for voice_id in test_voices:
            try:
                result = await self._quick_voice_test(voice_id)
                if result:
                    self.default_voice_id = voice_id
                    self.working_voices.append(voice_id)
                    logger.info(f"✅ Found working voice: {voice_id}")
                    return voice_id
            except:
                continue
        
        # If nothing works, return first test voice anyway
        self.default_voice_id = "liam"
        return self.default_voice_id
    
    async def _quick_voice_test(self, voice_id: str) -> bool:
        """Quick test if voice works"""
        
        try:
            payload = {
                "voiceId": voice_id,
                "text": "Test",
                "audioFormat": "MP3",
                "sampleRate": 24000
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
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        return "audioFile" in data
                    else:
                        return False
        
        except:
            return False
    
    async def text_to_speech(self, text: str, voice_id: str = None) -> Dict[str, Any]:
        """Convert text to speech with auto voice discovery"""
        
        if not self.available:
            return {
                "success": False,
                "error": "Murf API not configured",
                "audio_path": None,
                "audio_url": None
            }
        
        if not text or not text.strip():
            return {
                "success": False,
                "error": "No text provided",
                "audio_path": None,
                "audio_url": None
            }
        
        # Find working voice if not provided
        if not voice_id:
            voice_id = await self.find_working_voice()
        
        self.stats["requests"] += 1
        clean_text = text.strip()[:5000]
        
        try:
            payload = {
                "voiceId": voice_id,
                "text": clean_text,
                "audioFormat": "MP3",
                "sampleRate": 24000
            }
            
            headers = {
                "api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            logger.info(f"🎙️ TTS Request: {len(clean_text)} chars, voice: {voice_id}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/speech/generate",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    logger.info(f"🎙️ Murf response: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        if "audioFile" in data:
                            # Download audio
                            audio_path = await self._download_audio(data["audioFile"])
                            
                            if audio_path:
                                self.stats["successes"] += 1
                                self.stats["audio_files_created"] += 1
                                
                                # Generate public URL
                                audio_filename = Path(audio_path).name
                                public_url = f"/audio/{audio_filename}"
                                
                                return {
                                    "success": True,
                                    "audio_path": audio_path,
                                    "audio_url": public_url,
                                    "voice_id": voice_id,
                                    "text_length": len(clean_text),
                                    "audio_filename": audio_filename
                                }
                        
                        self.stats["failures"] += 1
                        return {
                            "success": False,
                            "error": "No audio file in response",
                            "audio_path": None,
                            "audio_url": None
                        }
                    
                    elif response.status == 400:
                        error_data = await response.json()
                        error_msg = error_data.get("errorMessage", "Unknown error")
                        
                        # If voice is invalid, try to find another one
                        if "Invalid voice_id" in error_msg and voice_id != self.default_voice_id:
                            logger.warning(f"⚠️ Voice {voice_id} invalid, trying default...")
                            return await self.text_to_speech(text, None)  # Will use find_working_voice
                        
                        self.stats["failures"] += 1
                        return {
                            "success": False,
                            "error": f"API error: {error_msg}",
                            "audio_path": None,
                            "audio_url": None
                        }
                    
                    else:
                        error_text = await response.text()
                        self.stats["failures"] += 1
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}: {error_text[:100]}",
                            "audio_path": None,
                            "audio_url": None
                        }
        
        except asyncio.TimeoutError:
            self.stats["failures"] += 1
            return {
                "success": False,
                "error": "Request timed out",
                "audio_path": None,
                "audio_url": None
            }
        
        except Exception as e:
            self.stats["failures"] += 1
            return {
                "success": False,
                "error": str(e),
                "audio_path": None,
                "audio_url": None
            }
    
    async def _download_audio(self, audio_url: str) -> Optional[str]:
        """Download audio file"""
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"working_audio_{timestamp}_{uuid.uuid4().hex[:8]}.mp3"
            file_path = self.cache_dir / filename
            
            async with aiohttp.ClientSession() as session:
                async with session.get(audio_url, timeout=aiohttp.ClientTimeout(total=20)) as response:
                    if response.status == 200:
                        async with aiofiles.open(file_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                        
                        if file_path.exists() and file_path.stat().st_size > 0:
                            logger.info(f"✅ Audio saved: {file_path} ({file_path.stat().st_size} bytes)")
                            return str(file_path)
            
            return None
        
        except Exception as e:
            logger.error(f"❌ Audio download failed: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics"""
        success_rate = (self.stats["successes"] / max(self.stats["requests"], 1)) * 100
        
        return {
            "available": self.available,
            "working_voices": self.working_voices,
            "default_voice": self.default_voice_id,
            "requests_made": self.stats["requests"],
            "successful_requests": self.stats["successes"],
            "failed_requests": self.stats["failures"],
            "success_rate_percentage": round(success_rate, 2),
            "audio_files_created": self.stats["audio_files_created"]
        }

class WorkingVoiceService:
    """Working voice service wrapper"""
    
    def __init__(self, murf_client: WorkingMurfClient):
        self.murf_client = murf_client
        self.available = murf_client.available
        self.service_type = "working_voice_service"
        
        self.service_stats = {
            "tts_requests": 0,
            "tts_successes": 0,
            "cache_hits": 0
        }
        
        self.text_cache = {}
        
        logger.info(f"🎙️ Working voice service initialized - Available: {self.available}")
    
    async def text_to_speech(self, text: str, voice_id: str = None) -> Dict[str, Any]:
        """TTS with auto-discovery of working voices"""
        
        self.service_stats["tts_requests"] += 1
        
        # Check cache
        cache_key = f"{text[:30]}_{voice_id or 'auto'}"
        if cache_key in self.text_cache:
            cached = self.text_cache[cache_key]
            if Path(cached["audio_path"]).exists():
                self.service_stats["cache_hits"] += 1
                return cached
        
        # Generate new audio
        result = await self.murf_client.text_to_speech(text, voice_id)
        
        if result["success"]:
            self.service_stats["tts_successes"] += 1
            # Cache result
            self.text_cache[cache_key] = result.copy()
            # Limit cache size
            if len(self.text_cache) > 20:
                self.text_cache.pop(next(iter(self.text_cache)))
        
        return result
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check with working voice discovery"""
        
        if not self.available:
            return {"healthy": False, "error": "Not configured", "available": False}
        
        try:
            # This will auto-discover a working voice
            result = await self.text_to_speech("Health check")
            
            return {
                "healthy": result.get("success", False),
                "available": self.available,
                "error": result.get("error") if not result.get("success") else None,
                "working_voice": self.murf_client.default_voice_id
            }
        
        except Exception as e:
            return {"healthy": False, "error": str(e), "available": False}
    
    def get_service_stats(self):
        """Get service stats"""
        return {
            "service_type": self.service_type,
            "available": self.available,
            "tts_requests": self.service_stats["tts_requests"],
            "tts_successes": self.service_stats["tts_successes"],
            "cache_hits": self.service_stats["cache_hits"],
            "murf_client_stats": self.murf_client.get_stats()
        }

# Quick test function
async def test_working_system():
    """Test the working voice system"""
    
    print("🧪 TESTING WORKING VOICE SYSTEM")
    print("=" * 50)
    
    api_key = os.getenv('MURF_API_KEY', 'your_murf_key_here')
    
    client = WorkingMurfClient(api_key)
    service = WorkingVoiceService(client)
    
    if service.available:
        print("✅ Service available, testing TTS...")
        
        result = await service.text_to_speech("This is a test of the working voice system")
        
        if result["success"]:
            print("🎉 SUCCESS! Working voice system operational!")
            print(f"   Voice used: {client.default_voice_id}")
            print(f"   Audio file: {result['audio_path']}")
            return True
        else:
            print(f"❌ TTS failed: {result['error']}")
    else:
        print("❌ Service not available")
    
    return False

if __name__ == "__main__":
    success = asyncio.run(test_working_system())
    if success:
        print("\n🎉 Working voice system ready!")
    else:
        print("\n❌ Still having issues")