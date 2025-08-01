#!/usr/bin/env python3
"""
Automated deployment script for Excel Interview System.
Handles Docker deployment with MCP integration.
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path

def check_prerequisites():
    """Check deployment prerequisites"""
    
    print("🔍 Checking deployment prerequisites...")
    
    # Check Docker
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
        print("✅ Docker is installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker is not installed or not in PATH")
        return False
    
    # Check Docker Compose
    try:
        subprocess.run(["docker", "compose", "version"], check=True, capture_output=True)
        print("✅ Docker Compose is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker Compose is not installed")
        return False
    
    # Check environment file
    if not Path(".env.production").exists():
        print("❌ .env.production file not found")
        print("💡 Create .env.production with production settings")
        return False
    
    print("✅ All prerequisites met")
    return True

def create_production_env():
    """Create production environment file"""
    
    env_file = Path(".env.production")
    
    if env_file.exists():
        print("✅ Production environment file already exists")
        return True
    
    print("📝 Creating production environment file...")
    
    # Get required values
    anthropic_key = input("🔑 Enter Anthropic API key: ").strip()
    domain = input("🌐 Enter your domain (e.g., example.com): ").strip()
    postgres_password = input("🔒 Enter PostgreSQL password: ").strip()
    acme_email = input("📧 Enter email for SSL certificates: ").strip()
    
    if not all([anthropic_key, domain, postgres_password, acme_email]):
        print("❌ All fields are required")
        return False
    
    env_content = f"""
# Production Environment Configuration
ANTHROPIC_API_KEY={anthropic_key}
POSTGRES_PASSWORD={postgres_password}
POSTGRES_USER=excel_admin
ACME_EMAIL={acme_email}
GRAFANA_PASSWORD=admin123

# Domain Configuration  
DOMAIN={domain}
API_DOMAIN=api.{domain}
FRONTEND_DOMAIN={domain}
MONITORING_DOMAIN=monitoring.{domain}

# MCP Configuration (optional)
MCP_SERVER_URL=https://mcp.{domain}
MCP_API_KEY=your_mcp_key_here
ENABLE_MCP_INTEGRATION=false

# Security
API_SECRET_KEY={os.urandom(32).hex()}
"""
    
    with open(env_file, "w") as f:
        f.write(env_content.strip())
    
    print("✅ Production environment file created")
    return True

def deploy_production():
    """Deploy production system"""
    
    print("🚀 Starting production deployment...")
    
    try:
        # Build and deploy with docker-compose
        subprocess.run([
            "docker", "compose", 
            "-f", "docker-compose.production.yml",
            "--env-file", ".env.production",
            "up", "-d", "--build"
        ], check=True)
        
        print("✅ Production deployment started")
        
        # Wait for services to be healthy
        print("⏳ Waiting for services to be ready...")
        time.sleep(30)
        
        # Check service health
        result = subprocess.run([
            "docker", "compose", 
            "-f", "docker-compose.production.yml",
            "ps"
        ], capture_output=True, text=True)
        
        print("📊 Service Status:")
        print(result.stdout)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Deployment failed: {e}")
        return False

def show_deployment_info():
    """Show deployment information"""
    
    env_file = Path(".env.production")
    if not env_file.exists():
        return
    
    # Read domain from env file
    domain = "your-domain.com"  # Default
    
    try:
        with open(env_file) as f:
            for line in f:
                if line.startswith("DOMAIN="):
                    domain = line.split("=", 1)[1].strip()
                    break
    except:
        pass
    
    print("\n" + "=" * 50)
    print("🎉 Deployment Complete!")
    print("=" * 50)
    print(f"🌍 Frontend:    https://{domain}")
    print(f"🔧 API:        https://api.{domain}")
    print(f"📚 API Docs:   https://api.{domain}/docs")
    print(f"📊 Monitoring: https://monitoring.{domain}")
    print(f"🔍 Traefik:    https://traefik.{domain}")
    print("=" * 50)
    print("\n💡 Next steps:")
    print("1. Configure your DNS to point to this server")
    print("2. SSL certificates will be auto-generated")
    print("3. Monitor logs: docker compose -f docker-compose.production.yml logs -f")
    print("4. Scale if needed: docker compose -f docker-compose.production.yml up -d --scale excel-interview-api=3")

def main():
    """Main deployment function"""
    
    print("🚀 Excel Interview System - Production Deployment")
    print("=" * 50)
    
    if not check_prerequisites():
        sys.exit(1)
    
    if not create_production_env():
        sys.exit(1)
    
    if not deploy_production():
        sys.exit(1)
    
    show_deployment_info()

if __name__ == "__main__":
    main()