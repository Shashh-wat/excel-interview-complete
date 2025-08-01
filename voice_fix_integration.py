# voice_fix_integration.py - Voice System Integration Fix
"""
Import this to replace your broken voice system components
"""

from fixed_murf_client import FixedMurfAPIClient, FixedVoiceService

# For backwards compatibility - these replace your broken classes
MurfAPIClient = FixedMurfAPIClient
VoiceService = FixedVoiceService

def initialize_working_voice_system(api_key: str):
    """Initialize working voice system"""
    
    print("🎙️ Initializing FIXED voice system...")
    
    murf_client = FixedMurfAPIClient(api_key)
    voice_service = FixedVoiceService(murf_client)
    
    print(f"   Murf Client Available: {murf_client.available}")
    print(f"   Voice Service Available: {voice_service.available}")
    
    if not murf_client.available:
        print(f"   ⚠️ API Key Issue: {api_key[:15] if api_key else 'None'}...")
    
    return murf_client, voice_service

# Export the classes for direct replacement
__all__ = ['MurfAPIClient', 'VoiceService', 'FixedMurfAPIClient', 'FixedVoiceService']
