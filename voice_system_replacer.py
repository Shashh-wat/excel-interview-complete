# voice_system_replacer.py - Replace Your Voice System
"""
This script replaces your broken voice system with the fixed one.
Just run this script and restart your server!
"""

import os
import shutil
from pathlib import Path

def backup_original_main():
    """Backup your original main.py"""
    
    if Path("main.py").exists():
        backup_path = "main_backup.py"
        shutil.copy("main.py", backup_path)
        print(f"✅ Backed up original main.py to {backup_path}")
    else:
        print("❌ main.py not found!")
        return False
    return True

def create_voice_integration():
    """Create voice integration file"""
    
    integration_code = '''# voice_integration.py - Voice System Integration
"""
This file integrates the fixed voice system with your main.py
Import this instead of the broken voice components.
"""

from fixed_murf_client import FixedMurfAPIClient, FixedVoiceService

def create_working_voice_system(api_key: str):
    """Create a working voice system"""
    
    print(f"🎙️ Creating voice system with fixed API client...")
    
    # Create fixed components
    murf_client = FixedMurfAPIClient(api_key)
    voice_service = FixedVoiceService(murf_client)
    
    print(f"   Murf Client Available: {murf_client.available}")
    print(f"   Voice Service Available: {voice_service.available}")
    
    return {
        "murf_client": murf_client,
        "voice_service": voice_service
    }

# For backwards compatibility
MurfAPIClient = FixedMurfAPIClient
VoiceService = FixedVoiceService
'''
    
    with open("voice_integration.py", "w") as f:
        f.write(integration_code)
    
    print("✅ Created voice_integration.py")

def update_main_imports():
    """Update main.py to use fixed voice system"""
    
    try:
        # Read main.py
        with open("main.py", "r") as f:
            content = f.read()
        
        # Add import for fixed voice system at the top
        import_section = """
# FIXED VOICE SYSTEM IMPORT
try:
    from voice_integration import create_working_voice_system
    FIXED_VOICE_AVAILABLE = True
    print("✅ Fixed voice system imported")
except ImportError:
    FIXED_VOICE_AVAILABLE = False
    print("❌ Fixed voice system not available")
"""
        
        # Insert after existing imports
        if "from dotenv import load_dotenv" in content:
            content = content.replace(
                "from dotenv import load_dotenv\nload_dotenv()",
                f"from dotenv import load_dotenv\nload_dotenv(){import_section}"
            )
        
        # Replace voice system initialization in lifespan function
        old_voice_init = """        # Initialize services
        murf_client = MurfAPIClient(settings.murf_api_key)
        voice_service = VoiceService(murf_client)"""
        
        new_voice_init = """        # Initialize services with FIXED voice system
        if FIXED_VOICE_AVAILABLE:
            voice_components = create_working_voice_system(settings.murf_api_key)
            murf_client = voice_components["murf_client"]
            voice_service = voice_components["voice_service"]
            print("✅ Using FIXED voice system")
        else:
            murf_client = MurfAPIClient(settings.murf_api_key)
            voice_service = VoiceService(murf_client)
            print("⚠️ Using original voice system")"""
        
        content = content.replace(old_voice_init, new_voice_init)
        
        # Write updated main.py
        with open("main.py", "w") as f:
            f.write(content)
        
        print("✅ Updated main.py to use fixed voice system")
        return True
        
    except Exception as e:
        print(f"❌ Failed to update main.py: {e}")
        return False

def create_quick_test():
    """Create a quick test script"""
    
    test_code = '''# test_voice_fix.py - Test Fixed Voice System
"""
Quick test to verify the voice system is working
"""

import asyncio
from voice_integration import create_working_voice_system

async def test_voice():
    print("🧪 Testing Fixed Voice System")
    print("=" * 40)
    
    # Create voice system
    api_key = "ap2_efed6cf1-51d4-4390-989b-f2c4d112dc61"
    voice_components = create_working_voice_system(api_key)
    voice_service = voice_components["voice_service"]
    
    if voice_service.available:
        print("✅ Voice service is available!")
        
        # Test TTS
        result = await voice_service.text_to_speech("Testing the fixed voice system!")
        
        if result["success"]:
            print("🎉 SUCCESS! Voice synthesis working!")
            print(f"Audio file: {result['audio_path']}")
        else:
            print(f"❌ TTS failed: {result['error']}")
    else:
        print("❌ Voice service not available")

if __name__ == "__main__":
    asyncio.run(test_voice())
'''
    
    with open("test_voice_fix.py", "w") as f:
        f.write(test_code)
    
    print("✅ Created test_voice_fix.py")

def main():
    """Main replacement function"""
    
    print("🔧 VOICE SYSTEM REPLACER")
    print("=" * 40)
    
    # Step 1: Backup original
    print("\n1. Backing up original main.py...")
    if not backup_original_main():
        return
    
    # Step 2: Create integration
    print("\n2. Creating voice integration...")
    create_voice_integration()
    
    # Step 3: Update main.py
    print("\n3. Updating main.py...")
    if update_main_imports():
        print("✅ main.py updated successfully")
    else:
        print("❌ Failed to update main.py")
        print("📝 You may need to manually integrate the fixed voice system")
        return
    
    # Step 4: Create test
    print("\n4. Creating test script...")
    create_quick_test()
    
    print("\n🎉 VOICE SYSTEM REPLACEMENT COMPLETE!")
    print("=" * 40)
    print("\n📋 NEXT STEPS:")
    print("1. Test the fix: python test_voice_fix.py")
    print("2. Restart your server: python main.py")
    print("3. Check http://localhost:8000/health")
    print("4. Test voice at: http://localhost:8000/api/voice/stats")
    
    print("\n💡 If something goes wrong:")
    print("   - Restore backup: cp main_backup.py main.py")
    print("   - Check the files: fixed_murf_client.py, voice_integration.py")

if __name__ == "__main__":
    main()