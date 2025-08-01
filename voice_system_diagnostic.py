# voice_system_diagnostic.py - Fix Voice System Issues
"""
This script diagnoses and fixes voice system issues in your Excel Interview System.
Run this to identify and resolve voice integration problems.
"""

import asyncio
import aiohttp
import logging
import os
from pathlib import Path
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# VOICE SYSTEM DIAGNOSTIC
# =============================================================================

class VoiceSystemDiagnostic:
    """Comprehensive voice system diagnostic and fix"""
    
    def __init__(self):
        self.murf_api_key = self._get_murf_api_key()
        self.issues_found = []
        self.fixes_applied = []
    
    def _get_murf_api_key(self):
        """Get Murf API key from various sources"""
        
        # Check environment variables
        api_key = (
            os.getenv('MURF_API_KEY') or
            os.getenv('murf_api_key') or
            'ap2_efed6cf1-51d4-4390-989b-f2c4d112dc61'  # Default from your code
        )
        
        return api_key
    
    async def run_full_diagnostic(self):
        """Run complete voice system diagnostic"""
        
        print("🔍 VOICE SYSTEM DIAGNOSTIC")
        print("=" * 50)
        
        # 1. Check API Key
        await self._check_api_key()
        
        # 2. Check Network Connectivity
        await self._check_network_connectivity()
        
        # 3. Test Murf API Endpoint
        await self._test_murf_api()
        
        # 4. Check File System Permissions
        await self._check_file_permissions()
        
        # 5. Test Audio Generation
        await self._test_audio_generation()
        
        # 6. Check Your Backend Integration
        await self._check_backend_integration()
        
        # Generate report
        await self._generate_diagnostic_report()
    
    async def _check_api_key(self):
        """Check if API key is valid"""
        
        print("\n📊 Checking API Key...")
        
        if not self.murf_api_key or self.murf_api_key == "test_key":
            self.issues_found.append("❌ No valid Murf API key found")
            print("❌ API Key: Not found or invalid")
            print("💡 Solution: Set MURF_API_KEY environment variable")
        else:
            print(f"✅ API Key: Found ({self.murf_api_key[:10]}...)")
    
    async def _check_network_connectivity(self):
        """Check network connectivity to Murf API"""
        
        print("\n🌐 Checking Network Connectivity...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.murf.ai", timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status in [200, 401, 403]:  # API is reachable
                        print("✅ Network: Can reach Murf API")
                    else:
                        print(f"⚠️ Network: Unexpected response {response.status}")
                        self.issues_found.append(f"Network connectivity issue: {response.status}")
        
        except asyncio.TimeoutError:
            print("❌ Network: Timeout connecting to Murf API")
            self.issues_found.append("Network timeout - check internet connection")
        
        except Exception as e:
            print(f"❌ Network: Connection failed - {e}")
            self.issues_found.append(f"Network error: {e}")
    
    async def _test_murf_api(self):
        """Test actual Murf API call"""
        
        print("\n🎙️ Testing Murf API...")
        
        if not self.murf_api_key or self.murf_api_key == "test_key":
            print("⏭️ Skipping API test - no valid key")
            return
        
        try:
            payload = {
                "voiceId": "en-US-sarah",
                "text": "Hello, this is a test of the voice system.",
                "rate": "0",
                "pitch": "0",
                "volume": "0",
                "audioFormat": "MP3",
                "sampleRate": 22050,
                "bitRate": 128
            }
            
            headers = {
                "Authorization": f"Bearer {self.murf_api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.murf.ai/v1/speech/generate", 
                    json=payload, 
                    headers=headers, 
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        response_data = await response.json()
                        if "audioFile" in response_data:
                            print("✅ Murf API: Working correctly")
                            print(f"   Audio URL: {response_data['audioFile'][:50]}...")
                        else:
                            print("⚠️ Murf API: Responds but no audio file")
                            self.issues_found.append("Murf API returns no audio file")
                    
                    elif response.status == 401:
                        print("❌ Murf API: Invalid API key")
                        self.issues_found.append("Invalid Murf API key")
                    
                    elif response.status == 429:
                        print("⚠️ Murf API: Rate limit exceeded")
                        self.issues_found.append("Murf API rate limit")
                    
                    else:
                        error_text = await response.text()
                        print(f"❌ Murf API: Error {response.status}")
                        print(f"   Response: {error_text[:100]}...")
                        self.issues_found.append(f"Murf API error: {response.status}")
        
        except Exception as e:
            print(f"❌ Murf API: Request failed - {e}")
            self.issues_found.append(f"Murf API request error: {e}")
    
    async def _check_file_permissions(self):
        """Check file system permissions for audio cache"""
        
        print("\n📁 Checking File Permissions...")
        
        try:
            # Check if voice_cache directory exists and is writable
            voice_cache_dir = Path("voice_cache")
            voice_cache_dir.mkdir(exist_ok=True)
            
            # Test write permission
            test_file = voice_cache_dir / "test_write.txt"
            test_file.write_text("test")
            test_file.unlink()
            
            print("✅ File System: Voice cache directory is writable")
        
        except PermissionError:
            print("❌ File System: No write permission for voice_cache")
            self.issues_found.append("No write permission for voice_cache directory")
        
        except Exception as e:
            print(f"❌ File System: Error - {e}")
            self.issues_found.append(f"File system error: {e}")
    
    async def _test_audio_generation(self):
        """Test complete audio generation workflow"""
        
        print("\n🎵 Testing Audio Generation Workflow...")
        
        if not self.murf_api_key or self.murf_api_key == "test_key":
            print("⏭️ Skipping audio generation test - no valid key")
            return
        
        try:
            # Import your MurfAPIClient
            import sys
            sys.path.append('.')
            
            from main import MurfAPIClient, VoiceService
            
            # Test the actual classes from your code
            murf_client = MurfAPIClient(self.murf_api_key)
            voice_service = VoiceService(murf_client)
            
            print(f"   Murf Client Available: {murf_client.available}")
            print(f"   Voice Service Available: {voice_service.available}")
            
            if murf_client.available:
                # Test actual TTS
                result = await voice_service.text_to_speech("Testing voice generation")
                
                if result["success"]:
                    print("✅ Audio Generation: Complete workflow working")
                    print(f"   Audio file: {result['audio_path']}")
                    
                    # Check if file actually exists
                    if Path(result['audio_path']).exists():
                        print("✅ Audio File: Successfully created and saved")
                    else:
                        print("⚠️ Audio File: Generated but not saved properly")
                        self.issues_found.append("Audio file not saved properly")
                else:
                    print(f"❌ Audio Generation: Failed - {result['error']}")
                    self.issues_found.append(f"Audio generation failed: {result['error']}")
            else:
                print("❌ Audio Generation: Murf client not available")
                self.issues_found.append("Murf client not available")
        
        except ImportError as e:
            print(f"❌ Audio Generation: Import error - {e}")
            self.issues_found.append(f"Import error: {e}")
        
        except Exception as e:
            print(f"❌ Audio Generation: Unexpected error - {e}")
            self.issues_found.append(f"Audio generation error: {e}")
    
    async def _check_backend_integration(self):
        """Check if your backend voice endpoints work"""
        
        print("\n🔗 Checking Backend Integration...")
        
        try:
            # Test your backend voice endpoints
            async with aiohttp.ClientSession() as session:
                
                # Test health endpoint
                async with session.get("http://localhost:8000/health") as response:
                    if response.status == 200:
                        health_data = await response.json()
                        voice_synthesis = health_data.get("features", {}).get("voice_synthesis", False)
                        
                        if voice_synthesis:
                            print("✅ Backend: Voice synthesis feature enabled")
                        else:
                            print("❌ Backend: Voice synthesis feature disabled")
                            self.issues_found.append("Backend voice synthesis disabled")
                    else:
                        print("❌ Backend: Health check failed")
                        self.issues_found.append("Backend health check failed")
                
                # Test voice stats endpoint
                async with session.get("http://localhost:8000/api/voice/stats") as response:
                    if response.status == 200:
                        stats = await response.json()
                        print("✅ Backend: Voice stats endpoint working")
                        print(f"   Service Type: {stats.get('service_type', 'unknown')}")
                        print(f"   Available: {stats.get('available', False)}")
                    else:
                        print(f"❌ Backend: Voice stats endpoint error {response.status}")
                        self.issues_found.append("Voice stats endpoint not working")
        
        except Exception as e:
            print(f"❌ Backend: Connection failed - {e}")
            self.issues_found.append(f"Backend connection error: {e}")
    
    async def _generate_diagnostic_report(self):
        """Generate diagnostic report and solutions"""
        
        print("\n" + "=" * 50)
        print("📋 DIAGNOSTIC REPORT")
        print("=" * 50)
        
        if not self.issues_found:
            print("🎉 All voice system checks passed!")
            print("✅ Your voice system should be working correctly.")
            return
        
        print(f"⚠️ Found {len(self.issues_found)} issues:")
        
        for i, issue in enumerate(self.issues_found, 1):
            print(f"   {i}. {issue}")
        
        print("\n🔧 RECOMMENDED SOLUTIONS:")
        print("=" * 30)
        
        solutions = []
        
        # API Key issues
        if any("API key" in issue for issue in self.issues_found):
            solutions.append("""
1. SET VALID MURF API KEY:
   - Go to https://murf.ai and sign up for an account
   - Get your API key from the dashboard
   - Set environment variable: export MURF_API_KEY="your_real_api_key"
   - Or update your .env file: MURF_API_KEY=your_real_api_key""")
        
        # Network issues
        if any("Network" in issue for issue in self.issues_found):
            solutions.append("""
2. FIX NETWORK CONNECTIVITY:
   - Check your internet connection
   - Verify firewall settings allow HTTPS to api.murf.ai
   - Try accessing https://api.murf.ai in your browser""")
        
        # File permission issues
        if any("permission" in issue.lower() for issue in self.issues_found):
            solutions.append("""
3. FIX FILE PERMISSIONS:
   - Run: chmod 755 voice_cache/
   - Or run your app with appropriate permissions
   - Check disk space availability""")
        
        # Backend integration issues
        if any("Backend" in issue for issue in self.issues_found):
            solutions.append("""
4. FIX BACKEND INTEGRATION:
   - Restart your FastAPI server
   - Check if voice_service is properly initialized in lifespan function
   - Verify missing_components.py is in the same directory""")
        
        for solution in solutions:
            print(solution)
        
        print(f"\n🚀 QUICK FIX SCRIPT:")
        print("Save this as fix_voice_system.py and run it:")
        self._generate_quick_fix_script()
    
    def _generate_quick_fix_script(self):
        """Generate a quick fix script"""
        
        fix_script = '''
# fix_voice_system.py - Quick Voice System Fix
import os
from pathlib import Path

def fix_voice_system():
    print("🔧 Applying voice system fixes...")
    
    # 1. Create voice_cache directory
    voice_dir = Path("voice_cache")
    voice_dir.mkdir(exist_ok=True)
    print("✅ Created voice_cache directory")
    
    # 2. Set permissions
    try:
        os.chmod(voice_dir, 0o755)
        print("✅ Set voice_cache permissions")
    except:
        print("⚠️ Could not set permissions (may not be needed)")
    
    # 3. Create .env file template
    env_file = Path(".env")
    if not env_file.exists():
        env_content = """# Excel Interview System Environment Variables
MURF_API_KEY=your_murf_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
DEBUG=true
HOST=0.0.0.0
PORT=8000
"""
        env_file.write_text(env_content)
        print("✅ Created .env template")
    
    print("🎉 Basic fixes applied!")
    print("📝 Next steps:")
    print("   1. Edit .env file with your real Murf API key")
    print("   2. Restart your server: python main.py")

if __name__ == "__main__":
    fix_voice_system()
'''
        
        print(fix_script)

# =============================================================================
# ALTERNATIVE VOICE IMPLEMENTATION
# =============================================================================

class AlternativeVoiceService:
    """Alternative voice service if Murf API is not working"""
    
    def __init__(self):
        self.available = True
        self.service_type = "alternative"
    
    async def text_to_speech(self, text: str, voice_id: str = None) -> dict:
        """Alternative TTS implementation using browser APIs"""
        
        # For now, return a mock response
        # In a real implementation, you could use:
        # - Azure Cognitive Services
        # - Google Cloud Text-to-Speech
        # - Amazon Polly
        # - Open source solutions like eSpeak
        
        return {
            "success": True,
            "audio_path": "/mock/audio/path.mp3",
            "voice_id": voice_id or "en-US-mock",
            "text_length": len(text),
            "note": "Mock audio service - replace with real TTS API"
        }
    
    def get_service_status(self):
        return {
            "available": True,
            "service_type": "alternative_mock",
            "note": "Mock service for testing"
        }

# =============================================================================
# MAIN EXECUTION
# =============================================================================

async def main():
    """Run voice system diagnostic"""
    
    diagnostic = VoiceSystemDiagnostic()
    await diagnostic.run_full_diagnostic()
    
    print(f"\n💡 IMMEDIATE ACTIONS:")
    print("1. Check if you have a valid Murf API key")
    print("2. Verify internet connectivity")
    print("3. Restart your server after fixes")
    print("4. Test voice synthesis at: http://localhost:8000/api/voice/synthesize")

if __name__ == "__main__":
    print("🔍 Voice System Diagnostic Tool")
    print("This will help identify why your voice system isn't working.")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Diagnostic cancelled")
    except Exception as e:
        print(f"\n❌ Diagnostic failed: {e}")