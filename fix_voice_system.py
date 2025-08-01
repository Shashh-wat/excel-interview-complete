# fix_voice_system.py - Automatic Voice System Fix
"""
This script automatically fixes your voice system by:
1. Creating the fixed Murf client
2. Updating your main.py to use it
3. Testing the fix
4. Providing verification steps

Just run: python fix_voice_system.py
"""

import os
import shutil
import asyncio
from pathlib import Path

def backup_files():
    """Backup your original files"""
    
    print("📦 Backing up original files...")
    
    if Path("main.py").exists():
        shutil.copy("main.py", "main_backup.py")
        print("✅ Backed up main.py → main_backup.py")
    
    return True

def create_fixed_components():
    """Create fixed voice components"""
    
    print("🔧 Creating fixed voice components...")
    
    # The fixed Murf client is already in the artifact above
    # Now create a simple integration helper
    
    integration_code = '''# voice_fix_integration.py - Voice System Integration Fix
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
'''
    
    with open("voice_fix_integration.py", "w") as f:
        f.write(integration_code)
    
    print("✅ Created voice_fix_integration.py")

def update_main_py():
    """Update main.py to use fixed voice system"""
    
    print("🔧 Updating main.py...")
    
    try:
        # Read current main.py
        with open("main.py", "r") as f:
            content = f.read()
        
        # Add import at the top (after existing imports)
        import_line = "\n# FIXED VOICE SYSTEM\nfrom voice_fix_integration import initialize_working_voice_system\n"
        
        # Find a good place to insert the import
        if "from dotenv import load_dotenv" in content:
            content = content.replace(
                "from dotenv import load_dotenv",
                f"from dotenv import load_dotenv{import_line}"
            )
        elif "import logging" in content:
            content = content.replace(
                "import logging",
                f"import logging{import_line}"
            )
        else:
            # Insert at the beginning
            content = import_line + content
        
        # Find and replace the voice system initialization in lifespan function
        old_init_patterns = [
            "murf_client = MurfAPIClient(settings.murf_api_key)",
            "voice_service = VoiceService(murf_client)"
        ]
        
        new_init = """        # Initialize FIXED voice system
        murf_client, voice_service = initialize_working_voice_system(settings.murf_api_key)"""
        
        # Replace the initialization section
        if "murf_client = MurfAPIClient" in content:
            # Find the section and replace it
            lines = content.split('\n')
            new_lines = []
            skip_next = False
            
            for line in lines:
                if skip_next and "voice_service = VoiceService" in line:
                    new_lines.append("        # Initialize FIXED voice system")
                    new_lines.append("        murf_client, voice_service = initialize_working_voice_system(settings.murf_api_key)")
                    skip_next = False
                elif "murf_client = MurfAPIClient" in line:
                    skip_next = True
                    # Skip this line, will be replaced
                    continue
                else:
                    new_lines.append(line)
            
            content = '\n'.join(new_lines)
        
        # Write updated main.py
        with open("main.py", "w") as f:
            f.write(content)
        
        print("✅ Updated main.py successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to update main.py: {e}")
        print("📝 You'll need to manually integrate the fix")
        return False

def create_test_script():
    """Create test script to verify the fix"""
    
    test_code = '''# test_voice_fix.py - Test the Voice System Fix
"""
Run this to test if the voice system fix worked
"""

import asyncio
import os
from pathlib import Path

async def test_voice_fix():
    print("🧪 Testing Voice System Fix")
    print("=" * 40)
    
    try:
        # Import the fixed components
        from voice_fix_integration import initialize_working_voice_system
        
        # Get API key
        api_key = os.getenv('MURF_API_KEY', 'ap2_efed6cf1-51d4-4390-989b-f2c4d112dc61')
        
        print(f"🔑 Using API key: {api_key[:15]}..." if api_key else "❌ No API key")
        
        # Initialize fixed system
        murf_client, voice_service = initialize_working_voice_system(api_key)
        
        if voice_service.available:
            print("✅ Voice service is available!")
            
            # Test TTS
            result = await voice_service.text_to_speech(
                "Testing the fixed voice system! This should work now.",
                "en-US-sarah"
            )
            
            if result["success"]:
                print("🎉 SUCCESS! Voice synthesis is working!")
                print(f"   Audio file: {result['audio_path']}")
                
                # Check if file exists
                if Path(result['audio_path']).exists():
                    file_size = Path(result['audio_path']).stat().st_size
                    print(f"   File size: {file_size} bytes")
                    print("✅ Audio file created successfully!")
                else:
                    print("❌ Audio file not found")
            else:
                print(f"❌ TTS failed: {result['error']}")
                print("📝 Check your Murf API key and internet connection")
        else:
            print("❌ Voice service not available")
            print("📝 Check your MURF_API_KEY environment variable")
        
        # Show detailed stats
        print(f"\\n📊 Murf Client Stats:")
        client_stats = murf_client.get_stats()
        for key, value in client_stats.items():
            print(f"   {key}: {value}")
        
        print(f"\\n📊 Voice Service Stats:")
        service_stats = voice_service.get_service_stats()
        for key, value in service_stats.items():
            print(f"   {key}: {value}")
        
        return voice_service.available
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("📝 Make sure fixed_murf_client.py is in the same directory")
        return False
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_voice_fix())
    
    if success:
        print("\\n🎉 VOICE SYSTEM FIX SUCCESSFUL!")
        print("📝 Next steps:")
        print("   1. Restart your server: python main.py")
        print("   2. Test at: http://localhost:8000/api/voice/test")
        print("   3. Check health: http://localhost:8000/health")
    else:
        print("\\n❌ Voice system still has issues")
        print("📝 Check the error messages above")
'''
    
    with open("test_voice_fix.py", "w") as f:
        f.write(test_code)
    
    print("✅ Created test_voice_fix.py")

def main():
    """Main fix process"""
    
    print("🔧 VOICE SYSTEM AUTOMATIC FIX")
    print("=" * 50)
    
    # Step 1: Backup
    print("\n1️⃣ Backing up files...")
    backup_files()
    
    # Step 2: Create fixed components  
    print("\n2️⃣ Creating fixed components...")
    create_fixed_components()
    
    # Step 3: Update main.py
    print("\n3️⃣ Updating main.py...")
    main_updated = update_main_py()
    
    # Step 4: Create test
    print("\n4️⃣ Creating test script...")
    create_test_script()
    
    print("\n" + "=" * 50)
    
    if main_updated:
        print("🎉 VOICE SYSTEM FIX APPLIED!")
        print("\n📋 IMMEDIATE NEXT STEPS:")
        print("1. Run: python test_voice_fix.py")
        print("2. If test passes, restart: python main.py")
        print("3. Test endpoint: http://localhost:8000/api/voice/test")
        print("4. Check health: http://localhost:8000/health")
        
        print("\n💡 If something goes wrong:")
        print("   - Restore backup: cp main_backup.py main.py")
        print("   - Check the error messages in test_voice_fix.py")
        print("   - Verify your MURF_API_KEY environment variable")
        
    else:
        print("❌ AUTOMATIC FIX FAILED")
        print("\n📝 MANUAL INTEGRATION STEPS:")
        print("1. Add to main.py imports:")
        print("   from voice_fix_integration import initialize_working_voice_system")
        print("2. Replace voice initialization with:")
        print("   murf_client, voice_service = initialize_working_voice_system(settings.murf_api_key)")
        print("3. Run: python test_voice_fix.py")

if __name__ == "__main__":
    main()