# one_line_fix.py - One Line Voice Fix
"""
Changes just one line in your existing fixed_murf_client.py
"""

def fix_one_line():
    """Fix one line in fixed_murf_client.py"""
    
    print("🔧 ONE LINE FIX")
    print("=" * 30)
    
    try:
        # Read fixed_murf_client.py
        with open("fixed_murf_client.py", "r") as f:
            content = f.read()
        
        # Replace the voice ID line
        old_line = 'self.default_voice_id = "natalie"'
        new_line = 'self.default_voice_id = "en-US-cooper"'
        
        if old_line in content:
            content = content.replace(old_line, new_line)
            print(f"✅ Found and replacing: {old_line}")
            print(f"   With: {new_line}")
        else:
            # Try other patterns
            patterns = [
                'self.default_voice_id = "en-US-sarah"',
                'self.default_voice_id = "liam"'
            ]
            
            for pattern in patterns:
                if pattern in content:
                    content = content.replace(pattern, new_line)
                    print(f"✅ Found and replacing: {pattern}")
                    print(f"   With: {new_line}")
                    break
            else:
                print("❌ Could not find voice ID line to replace")
                return False
        
        # Write back
        with open("fixed_murf_client.py", "w") as f:
            f.write(content)
        
        print("✅ Updated fixed_murf_client.py")
        print("🚀 Now restart: python main.py")
        return True
        
    except Exception as e:
        print(f"❌ Fix failed: {e}")
        return False

if __name__ == "__main__":
    fix_one_line()