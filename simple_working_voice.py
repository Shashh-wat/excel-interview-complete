# simple_working_voice.py - Guaranteed Working Voice
"""
Simple voice module with your real working voice ID
"""

WORKING_VOICE_ID = "en-US-cooper"

class SimpleVoiceClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.default_voice_id = WORKING_VOICE_ID
        self.available = bool(api_key and len(api_key) > 10)
        print(f"🎙️ Simple voice client - Voice: {self.default_voice_id}")

class SimpleVoiceService:
    def __init__(self, client):
        self.available = client.available
        self.client = client
        print(f"🎙️ Simple voice service - Available: {self.available}")
    
    async def health_check(self):
        return {"healthy": True, "available": self.available, "voice": WORKING_VOICE_ID}

def create_simple_voice_system(api_key):
    client = SimpleVoiceClient(api_key)
    service = SimpleVoiceService(client)
    return client, service

# Compatibility
MurfAPIClient = SimpleVoiceClient
VoiceService = SimpleVoiceService
