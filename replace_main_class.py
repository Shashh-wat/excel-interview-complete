# replace_main_class.py - Replace Broken Class in Main.py
"""
Replaces the broken MurfAPIClient class in your main.py with the working one
"""

import shutil

def replace_broken_class():
    """Replace the broken MurfAPIClient class in main.py"""
    
    print("🔧 REPLACING BROKEN CLASS IN MAIN.PY")
    print("=" * 50)
    
    # Backup
    shutil.copy("main.py", "main_backup_class_fix.py")
    print("✅ Backed up main.py")
    
    # Read main.py
    with open("main.py", "r") as f:
        content = f.read()
    
    # Find the broken MurfAPIClient class
    if "class MurfAPIClient:" in content:
        print("✅ Found broken MurfAPIClient class in main.py")
        
        # Find the start and end of the class
        lines = content.split('\n')
        class_start = -1
        class_end = -1
        
        for i, line in enumerate(lines):
            if "class MurfAPIClient:" in line:
                class_start = i
            elif class_start != -1 and line.startswith('class ') and 'MurfAPIClient' not in line:
                class_end = i
                break
        
        if class_start != -1:
            if class_end == -1:
                # Class goes to end of file or next major section
                for i in range(class_start + 1, len(lines)):
                    if lines[i].startswith('# =============') or lines[i].startswith('class '):
                        class_end = i
                        break
                if class_end == -1:
                    class_end = len(lines)
            
            print(f"✅ Found class from line {class_start + 1} to {class_end}")
            
            # Replace with working class
            working_class = '''class MurfAPIClient:
    """WORKING Murf API client that actually works"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.murf.ai/v1"
        self.available = bool(api_key and api_key != "test_key")
        self.default_voice_id = "en-US-cooper"  # YOUR WORKING VOICE ID
        self.logger = logging.getLogger(__name__)
        
        # Ensure voice cache directory exists
        self.cache_dir = Path("voice_cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        # API stats tracking
        self.api_stats = {
            "requests_made": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_audio_files": 0,
            "total_characters_processed": 0
        }
        
    async def text_to_speech(self, text: str, voice_id: str = None) -> Dict[str, Any]:
        """Generate speech with working headers and voice ID"""
        
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
        
        # Clean and limit text
        clean_text = text.strip()[:5000]
        
        self.api_stats["requests_made"] += 1
        self.api_stats["total_characters_processed"] += len(clean_text)
        
        try:
            payload = {
                "voiceId": voice_id or self.default_voice_id,
                "text": clean_text,
                "audioFormat": "MP3",
                "sampleRate": 24000
            }
            
            headers = {
                "api-key": self.api_key,  # CORRECT HEADER FORMAT
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/speech/generate", 
                    json=payload, 
                    headers=headers, 
                    timeout=aiohttp.ClientTimeout(total=45)
                ) as response:
                    
                    if response.status == 200:
                        response_data = await response.json()
                        
                        if "audioFile" in response_data:
                            # Download and store audio file
                            audio_file_url = response_data["audioFile"]
                            local_audio_path = await self._download_audio(audio_file_url)
                            
                            if local_audio_path:
                                # Generate public URL for frontend
                                audio_filename = Path(local_audio_path).name
                                public_audio_url = f"/audio/{audio_filename}"
                                
                                self.api_stats["successful_requests"] += 1
                                self.api_stats["total_audio_files"] += 1
                                
                                return {
                                    "success": True,
                                    "audio_path": local_audio_path,
                                    "audio_url": public_audio_url,
                                    "voice_id": voice_id or self.default_voice_id,
                                    "text_length": len(clean_text),
                                    "audio_filename": audio_filename
                                }
                            else:
                                self.api_stats["failed_requests"] += 1
                                return {
                                    "success": False,
                                    "error": "Failed to download audio file",
                                    "audio_path": None,
                                    "audio_url": None
                                }
                        else:
                            self.api_stats["failed_requests"] += 1
                            return {
                                "success": False,
                                "error": "No audio file in Murf response",
                                "audio_path": None,
                                "audio_url": None
                            }
                    else:
                        self.api_stats["failed_requests"] += 1
                        error_text = await response.text()
                        self.logger.error(f"Murf API error {response.status}: {error_text}")
                        return {
                            "success": False,
                            "error": f"Murf API error: {response.status} - {error_text}",
                            "audio_path": None,
                            "audio_url": None
                        }
                        
        except asyncio.TimeoutError:
            self.api_stats["failed_requests"] += 1
            self.logger.error("Murf API timeout")
            return {
                "success": False,
                "error": "Murf API timeout - request took too long",
                "audio_path": None,
                "audio_url": None
            }
        except Exception as e:
            self.api_stats["failed_requests"] += 1
            self.logger.error(f"Murf API failed: {e}")
            return {
                "success": False,
                "error": f"Murf API error: {str(e)}",
                "audio_path": None,
                "audio_url": None
            }
    
    async def _download_audio(self, audio_url: str) -> str:
        """Download audio file and store locally"""
        
        try:
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"murf_audio_{timestamp}_{uuid.uuid4().hex[:8]}.mp3"
            file_path = self.cache_dir / filename
            
            # Download file with timeout
            async with aiohttp.ClientSession() as session:
                async with session.get(audio_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        async with aiofiles.open(file_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                        
                        self.logger.info(f"✅ Audio downloaded: {file_path}")
                        return str(file_path)
                    else:
                        raise Exception(f"Download failed with status {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Audio download failed: {e}")
            return None
    
    def get_default_voices(self) -> List[Dict[str, str]]:
        """Get available Murf voices"""
        return [
            {"id": "en-US-cooper", "name": "Cooper", "language": "English (US)", "gender": "Male", "description": "Professional, clear"},
            {"id": "en-US-imani", "name": "Imani", "language": "English (US)", "gender": "Female", "description": "Warm, engaging"},
            {"id": "en-UK-hazel", "name": "Hazel", "language": "English (UK)", "gender": "Female", "description": "Sophisticated, British"},
        ]
    
    def get_api_stats(self) -> Dict[str, Any]:
        """Get API usage statistics"""
        success_rate = 0
        if self.api_stats["requests_made"] > 0:
            success_rate = (self.api_stats["successful_requests"] / self.api_stats["requests_made"]) * 100
        
        return {
            "requests_made": self.api_stats["requests_made"],
            "successful_requests": self.api_stats["successful_requests"],
            "failed_requests": self.api_stats["failed_requests"],
            "success_rate_percentage": round(success_rate, 2),
            "total_audio_files": self.api_stats["total_audio_files"],
            "total_characters_processed": self.api_stats["total_characters_processed"],
            "cache_files_count": len(list(self.cache_dir.glob("*.mp3"))) if self.cache_dir.exists() else 0
        }'''
            
            # Replace the broken class
            new_lines = lines[:class_start] + [working_class] + lines[class_end:]
            new_content = '\n'.join(new_lines)
            
            # Write back
            with open("main.py", "w") as f:
                f.write(new_content)
            
            print("✅ Replaced broken MurfAPIClient class with working one")
            print("🎯 Fixed issues:")
            print("   ✅ Voice ID: en-US-sarah → en-US-cooper")
            print("   ✅ Headers: Authorization Bearer → api-key")
            print("   ✅ Sample Rate: 22050 → 24000")
            
            return True
        
        else:
            print("❌ Could not find class boundaries")
            return False
    
    else:
        print("❌ MurfAPIClient class not found in main.py")
        return False

def main():
    """Main execution"""
    
    success = replace_broken_class()
    
    if success:
        print("\n🎉 BROKEN CLASS REPLACED!")
        print("=" * 40)
        print("✅ Your main.py now has the working MurfAPIClient")
        print("✅ Uses correct voice ID: en-US-cooper")
        print("✅ Uses correct API headers")
        
        print("\n🚀 RESTART YOUR SERVER:")
        print("python main.py")
        
        print("\n👀 Look for:")
        print("INFO:main:🎙️ Voice service: ✅ Healthy")
        
    else:
        print("\n❌ Could not replace class automatically")
        print("📝 Manual fix:")
        print("1. In main.py, find: self.default_voice_id = \"en-US-sarah\"")
        print("2. Change to: self.default_voice_id = \"en-US-cooper\"")
        print("3. Find: \"Authorization\": f\"Bearer {self.api_key}\"")
        print("4. Change to: \"api-key\": self.api_key")
        print("5. Find: \"sampleRate\": 22050")
        print("6. Change to: \"sampleRate\": 24000")

if __name__ == "__main__":
    main()