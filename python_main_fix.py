# direct_main_fix.py - Simple Main.py Voice Fix
"""
Directly fixes your main.py to use the working voice ID we found.
No new files, just fixes what you have.
"""

import shutil

def fix_main_py():
    """Fix your actual main.py file"""
    
    print("🔧 FIXING YOUR MAIN.PY DIRECTLY")
    print("=" * 40)
    
    # Backup
    shutil.copy("main.py", "main_backup_final.py")
    print("✅ Backed up main.py")
    
    # Read main.py
    with open("main.py", "r") as f:
        content = f.read()
    
    # Simple fix: Add voice override right after murf_client creation
    # Find the line that creates murf_client and add override after it
    
    lines = content.split('\n')
    new_lines = []
    voice_override_added = False
    
    for line in lines:
        new_lines.append(line)
        
        # After any line that creates murf_client, add the voice override
        if ("murf_client = " in line and "MurfAPIClient" in line) or \
           ("murf_client," in line and "initialize_working_voice_system" in line):
            if not voice_override_added:
                new_lines.append("        # FIX: Use working voice ID from your account")
                new_lines.append('        murf_client.default_voice_id = "en-US-cooper"')
                new_lines.append('        print(f"🎙️ Forced voice ID to: {murf_client.default_voice_id}")')
                voice_override_added = True
                print("✅ Added voice ID override")
    
    if not voice_override_added:
        print("⚠️ Could not find murf_client creation line")
        print("📝 Manual fix needed:")
        print('   Add this after murf_client creation:')
        print('   murf_client.default_voice_id = "en-US-cooper"')
        return False
    
    # Write fixed main.py
    with open("main.py", "w") as f:
        f.write('\n'.join(new_lines))
    
    print("✅ Fixed main.py")
    return True

def main():
    """Main fix"""
    
    success = fix_main_py()
    
    if success:
        print("\n🎉 MAIN.PY FIXED!")
        print("=" * 30)
        print("✅ Added voice ID override to your existing main.py")
        print('✅ Will use voice: "en-US-cooper"')
        
        print("\n🚀 RESTART NOW:")
        print("python main.py")
        
        print("\n👀 Look for:")
        print("🎙️ Forced voice ID to: en-US-cooper")
        print("🎙️ Voice service: ✅ Healthy")
        
    else:
        print("\n📝 MANUAL FIX:")
        print("1. Open main.py")
        print("2. Find the line: murf_client = MurfAPIClient(...)")
        print("3. Add after it: murf_client.default_voice_id = \"en-US-cooper\"")
        print("4. Save and restart")

if __name__ == "__main__":
    main()