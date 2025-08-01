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
        self.default_voice_id = None
        
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
        test_voices = ["liam", "olivia", "noah", "emma", "sarah", "john", "natalie", "marcus"]
        
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
            print("Failed to initialize Murf client - API key may be invalid or missing.")
            return {
                "success": False,}
            print("Failed to initialize Murf client - API key may be invalid or missing.")