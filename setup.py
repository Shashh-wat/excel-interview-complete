#!/usr/bin/env python3
# setup.py - Quick Setup Script for Voice Interview System
"""
Quick setup script to get your voice interview system running
Handles environment setup, dependency installation, and initial configuration
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_header():
    """Print setup header"""
    print("🎙️ Excel Voice Interview System - Quick Setup")
    print("=" * 60)

def check_python_version():
    """Check Python version"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required. Current version:", sys.version)
        return False
    print(f"✅ Python version: {sys.version_info.major}.{sys.version_info.minor}")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    
    try:
        # Core requirements
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True)
        
        core_packages = [
            "fastapi>=0.104.1",
            "uvicorn[standard]>=0.24.0",
            "python-multipart>=0.0.6",
            "aiofiles>=23.2.1",
            "python-dotenv>=1.0.0",
            "anthropic>=0.7.8",
            "streamlit>=1.28.0",
            "requests>=2.31.0"
        ]
        
        for package in core_packages:
            print(f"Installing {package}...")
            subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)
        
        print("✅ Core dependencies installed")
        
        # Optional voice dependencies
        print("\n🎙️ Installing voice dependencies...")
        voice_packages = [
            "elevenlabs>=0.2.26",
            "openai-whisper>=20231117",
            "sounddevice>=0.4.6",
            "soundfile>=0.12.1",
            "librosa>=0.10.1"
        ]
        
        for package in voice_packages:
            try:
                print(f"Installing {package}...")
                subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)
            except subprocess.CalledProcessError as e:
                print(f"⚠️ Failed to install {package}: {e}")
                print("   Voice features may be limited")
        
        print("✅ Voice dependencies installation completed")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Dependency installation failed: {e}")
        return False

def setup_environment_file():
    """Setup environment file"""
    print("\n📝 Setting up environment file...")
    
    env_file = Path(".env")
    env_template = Path(".env.template")
    
    if env_file.exists():
        print("⚠️ .env file already exists")
        response = input("Overwrite existing .env file? (y/N): ")
        if response.lower() != 'y':
            print("Keeping existing .env file")
            return True
    
    # Create basic .env file
    env_content = '''# Excel Voice Interview System Configuration
# IMPORTANT: Add your actual API keys below

# Application Settings
APP_NAME="Excel Voice Interview System"
APP_VERSION="4.0.0-fixed"
DEBUG=true
ENVIRONMENT=development

# Server Settings
HOST=0.0.0.0
PORT=8000
RELOAD=true

# API Keys (REQUIRED - Replace with your actual keys)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# Voice Settings
DEFAULT_VOICE_ID=21m00Tcm4TlvDq8ikWAM
MAX_AUDIO_DURATION_SECONDS=300
MAX_AUDIO_FILE_SIZE_MB=25

# File Storage
UPLOAD_DIR=uploads
VOICE_STORAGE_DIR=voice_interviews
QUESTION_BANK_PATH=question_bank.db
AUTO_SETUP_QUESTION_BANK=true

# CORS (for Streamlit)
ALLOWED_ORIGINS=*

# Development
ENABLE_DEV_ENDPOINTS=true
'''
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print(f"✅ Created {env_file}")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def create_directories():
    """Create required directories"""
    print("\n📁 Creating directories...")
    
    directories = [
        "uploads",
        "voice_interviews", 
        "voice_cache",
        "temp_audio"
    ]
    
    for directory in directories:
        try:
            Path(directory).mkdir(exist_ok=True)
            print(f"✅ Created directory: {directory}")
        except Exception as e:
            print(f"⚠️ Failed to create {directory}: {e}")
    
    return True

def check_system_requirements():
    """Check system requirements"""
    print("\n🔍 Checking system requirements...")
    
    # Check FFmpeg (required for audio processing)
    try:
        subprocess.run(["ffmpeg", "-version"], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL, 
                      check=True)
        print("✅ FFmpeg available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️ FFmpeg not found - audio processing may be limited")
        print("   Install with: brew install ffmpeg (macOS) or apt install ffmpeg (Ubuntu)")
    
    return True

def test_basic_functionality():
    """Test basic functionality"""
    print("\n🧪 Testing basic functionality...")
    
    try:
        # Test imports
        print("Testing imports...")
        
        # Test evaluation engine import
        try:
            from evaluation_engine import EvaluationEngineFactory
            print("✅ Evaluation engine import successful")
        except ImportError as e:
            print(f"⚠️ Evaluation engine import failed: {e}")
        
        # Test voice components import
        try:
            from voice_interview_service import VoiceInterviewServiceFactory
            print("✅ Voice components import successful")
        except ImportError as e:
            print(f"⚠️ Voice components import failed: {e}")
        
        # Test models import
        try:
            from models import SkillCategory, DifficultyLevel
            print("✅ Models import successful")
        except ImportError as e:
            print(f"⚠️ Models import failed: {e}")
        
        print("✅ Basic functionality test completed")
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def provide_next_steps():
    """Provide next steps instructions"""
    print("\n🚀 Setup Complete! Next Steps:")
    print("=" * 60)
    
    print("\n1. 🔑 Add your API keys to .env file:")
    print("   - Get Anthropic API key: https://console.anthropic.com")
    print("   - Get ElevenLabs API key: https://elevenlabs.io")
    print("   - Edit .env file and replace 'your_*_api_key_here' with actual keys")
    
    print("\n2. 🚀 Start the backend server:")
    print("   python voice_main_fixed.py")
    
    print("\n3. 🎨 Start the Streamlit frontend (in another terminal):")
    print("   streamlit run streamlit_app.py")
    
    print("\n4. 🔍 Test the system:")
    print("   - Backend health: http://localhost:8000/health")
    print("   - Frontend: http://localhost:8501")
    print("   - API docs: http://localhost:8000/docs")
    
    print("\n5. 🎯 Choose your interview mode:")
    print("   - 🎙️ Voice Interview: Full AI conversation")
    print("   - 📝 Text Interview: Traditional typing")
    print("   - 🔄 Hybrid: Mix of voice and text")
    
    print("\n💡 Troubleshooting:")
    print("   - Check .env file has your API keys")
    print("   - Verify all dependencies installed: pip install -r requirements.txt")
    print("   - Check logs for detailed error information")
    print("   - Visit /api/dev/component-status for detailed system status")

def main():
    """Main setup function"""
    print_header()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Setup failed at dependency installation")
        sys.exit(1)
    
    # Setup environment
    if not setup_environment_file():
        print("❌ Setup failed at environment configuration")
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        print("❌ Setup failed at directory creation")
        sys.exit(1)
    
    # Check system requirements
    check_system_requirements()
    
    # Test basic functionality
    test_basic_functionality()
    
    # Provide next steps
    provide_next_steps()
    
    print("\n🎉 Setup completed successfully!")
    print("🔑 Don't forget to add your API keys to the .env file!")

if __name__ == "__main__":
    main()