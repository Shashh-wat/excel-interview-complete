#!/usr/bin/env python3
# run_system.py - FIXED Excel Interview System Startup Script
"""
Startup script for the FIXED Excel Interview System.
This script checks dependencies and starts the system properly.
"""

import os
import sys
import logging
import asyncio
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_python_version():
    """Check Python version compatibility"""
    if sys.version_info < (3, 8):
        logger.error("Python 3.8 or higher is required")
        return False
    
    logger.info(f"✅ Python version: {sys.version}")
    return True

def check_dependencies():
    """Check if required dependencies are available"""
    
    required_packages = [
        'fastapi',
        'uvicorn', 
        'aiofiles',
        'anthropic',
        'openpyxl',
        'pydantic'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"✅ {package} - available")
        except ImportError:
            logger.warning(f"❌ {package} - missing")
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Missing packages: {', '.join(missing_packages)}")
        logger.info("Install with: pip install -r requirements.txt")
        return False
    
    return True

def check_environment():
    """Check environment setup"""
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check for API key with multiple possible names
    api_key = (
        os.getenv('ANTHROPIC_API_KEY') or 
        os.getenv('anthropic_api_key') or 
        os.getenv('ANTHROPIC_KEY')
    )
    
    if not api_key or api_key == 'test_key':
        logger.warning("⚠️  Anthropic API key not found in environment")
        logger.info("💡 To enable Claude evaluation:")
        logger.info("   1. Set ANTHROPIC_API_KEY in your .env file")
        logger.info("   2. Or set it as environment variable:")
        logger.info("      export ANTHROPIC_API_KEY=your_api_key")
        logger.info("   3. System will use fallback evaluation mode")
    else:
        # Show masked version for security
        masked_key = f"{api_key[:8]}...{api_key[-8:]}"
        logger.info(f"✅ Anthropic API key found: {masked_key}")
    
    # Check .env file exists
    env_file = Path('.env')
    if env_file.exists():
        logger.info("✅ .env file found")
        
        # Read and validate .env content
        try:
            with open('.env', 'r') as f:
                env_content = f.read()
                
            if 'ANTHROPIC_API_KEY' in env_content or 'anthropic_api_key' in env_content:
                logger.info("✅ API key variable found in .env")
            else:
                logger.warning("⚠️  No API key variable found in .env file")
                
        except Exception as e:
            logger.warning(f"⚠️  Could not read .env file: {e}")
    else:
        logger.warning("⚠️  .env file not found")
        logger.info("💡 Create a .env file with your configuration")
    
    # Check upload directory
    upload_dir = Path(os.getenv('UPLOAD_DIR', 'uploads'))
    upload_dir.mkdir(exist_ok=True)
    logger.info(f"✅ Upload directory: {upload_dir.absolute()}")
    
    return True

def check_file_structure():
    """Check that all required files are present"""
    
    required_files = [
        'main.py',
        'evaluation_engine.py',
        'interview_orchestrator.py',
        'models.py',
        'requirements.txt'
    ]
    
    missing_files = []
    
    for file_name in required_files:
        file_path = Path(file_name)
        if file_path.exists():
            logger.info(f"✅ {file_name} - found")
        else:
            logger.error(f"❌ {file_name} - missing")
            missing_files.append(file_name)
    
    if missing_files:
        logger.error(f"Missing files: {', '.join(missing_files)}")
        return False
    
    return True

async def test_system_integration():
    """Test basic system integration"""
    
    try:
        logger.info("🧪 Testing system integration...")
        
        # Test import of main components
        from evaluation_engine import EvaluationEngineFactory
        from interview_orchestrator import InterviewWorkflowFactory
        from models import SkillCategory, QuestionType
        
        logger.info("✅ All components import successfully")
        
        # Test evaluation engine
        engine = EvaluationEngineFactory.create_development_engine()
        health = await engine.health_check()
        logger.info(f"✅ Evaluation engine health: {health['status']} ({health['health_percentage']}%)")
        
        # Test orchestrator
        orchestrator = InterviewWorkflowFactory.create_complete_workflow(evaluation_engine=engine)
        logger.info("✅ Interview orchestrator created successfully")
        
        # Quick evaluation test
        test_question = {
            "id": "startup_test",
            "text": "Test question",
            "type": "free_text",
            "expected_keywords": ["test"]
        }
        
        eval_result = await engine.evaluate_response(
            question=test_question,
            text_response="This is a test response"
        )
        
        logger.info(f"✅ Test evaluation: {eval_result.get('score', 0):.1f}/5.0")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Integration test failed: {e}")
        return False

def start_development_server():
    """Start the development server"""
    
    try:
        import uvicorn
        
        logger.info("🚀 Starting Excel Interview System...")
        logger.info("=" * 60)
        logger.info("📍 Server will start at: http://0.0.0.0:8000")
        logger.info("📚 API documentation: http://0.0.0.0:8000/docs")
        logger.info("🔍 Health check: http://0.0.0.0:8000/health")
        logger.info("🛠️  Component check: http://0.0.0.0:8000/api/dev/components")
        logger.info("🧪 Integration test: http://0.0.0.0:8000/api/dev/test-integration")
        logger.info("=" * 60)
        
        # Import the FastAPI app
        from main import app
        
        # Start the server
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        logger.info("\n🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")
        return False
    
    return True

def main():
    """Main startup function"""
    
    print("🚀 FIXED Excel Interview System - Startup")
    print("=" * 50)
    
    # Pre-flight checks
    checks = [
        ("Python version", check_python_version),
        ("File structure", check_file_structure),
        ("Dependencies", check_dependencies),
        ("Environment", check_environment)
    ]
    
    for check_name, check_func in checks:
        print(f"\n🔍 Checking {check_name}...")
        if not check_func():
            print(f"❌ {check_name} check failed")
            sys.exit(1)
        print(f"✅ {check_name} check passed")
    
    # Integration test
    print(f"\n🧪 Running integration test...")
    integration_success = asyncio.run(test_system_integration())
    
    if not integration_success:
        print("❌ Integration test failed")
        print("\n💡 Troubleshooting:")
        print("  1. Check that all files are present")
        print("  2. Install dependencies: pip install -r requirements.txt")
        print("  3. Set ANTHROPIC_API_KEY environment variable")
        print("  4. Ensure Python 3.8+ is being used")
        sys.exit(1)
    
    print("✅ Integration test passed")
    print("\n🎉 All checks passed! Starting server...")
    
    # Start the server
    start_development_server()

if __name__ == "__main__":
    main()