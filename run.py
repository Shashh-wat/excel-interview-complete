#!/usr/bin/env python3
"""
Simple development runner for the Excel Interview System.
Run this instead of main.py for easier development setup.
"""

import os
import sys
import subprocess
from pathlib import Path

def setup_environment():
    """Set up development environment"""
    
    # Create required directories
    directories = ["data", "uploads", "logs", "cache", "backups"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # Check for .env file
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  .env file not found!")
        print("📋 Copy .env.example to .env and configure your settings")
        
        # Copy example if it exists
        example_file = Path(".env.example")
        if example_file.exists():
            import shutil
            shutil.copy(example_file, env_file)
            print("✅ Created .env from .env.example")
        
        return False
    
    # Check for required environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ["ANTHROPIC_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    return True

def start_redis():
    """Start Redis if not running"""
    
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis is running")
        return True
    except:
        print("⚠️  Redis not running. Starting with Docker...")
        try:
            subprocess.run(["docker", "run", "-d", "-p", "6379:6379", "--name", "excel-interview-redis", "redis:7-alpine"], check=True)
            print("✅ Redis started with Docker")
            return True
        except:
            print("❌ Failed to start Redis. Please start Redis manually or install Docker")
            print("💡 You can still run the system - it will work without Redis (using memory cache)")
            return False

def main():
    """Main development runner"""
    
    print("🚀 Excel Interview System - Development Setup")
    print("=" * 50)
    
    # Setup environment
    if not setup_environment():
        print("❌ Environment setup failed. Please fix the issues above.")
        sys.exit(1)
    
    # Start Redis (optional)
    start_redis()
    
    # Import and run the application
    print("\n🎯 Starting Excel Interview System...")
    print("📍 API will be available at: http://localhost:8000")
    print("📚 API documentation at: http://localhost:8000/docs")
    print("🔍 Health check at: http://localhost:8000/health")
    print("\n⭐ Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Run the FastAPI application
        os.system("python main.py")
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Excel Interview System...")
        print("✅ Goodbye!")

if __name__ == "__main__":
    main()