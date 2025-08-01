#!/usr/bin/env python3
"""
Quick integration test to verify all systems are working.
Run this after setting up the environment.
"""

import asyncio
import httpx
import json
from pathlib import Path

async def test_integration():
    """Test the complete integration"""
    
    print("🧪 Testing Excel Interview System Integration")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        
        # Test 1: Health check
        print("1️⃣ Testing health check...")
        try:
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ Health check passed - System healthy: {health_data['healthy']}")
            else:
                print(f"❌ Health check failed - Status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
        
        # Test 2: Start interview
        print("\n2️⃣ Testing interview start...")
        try:
            response = await client.post(f"{base_url}/api/interview/start", json={
                "candidate_name": "Test User",
                "preferred_difficulty": "intermediate"
            })
            if response.status_code == 200:
                interview_data = response.json()
                session_id = interview_data["session_id"]
                print(f"✅ Interview started - Session ID: {session_id}")
            else:
                print(f"❌ Interview start failed - Status: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Interview start error: {e}")
            return False
        
        # Test 3: Get interview status
        print("\n3️⃣ Testing interview status...")
        try:
            response = await client.get(f"{base_url}/api/interview/{session_id}/status")
            if response.status_code == 200:
                status_data = response.json()
                print(f"✅ Status retrieved - Status: {status_data['status']}")
            else:
                print(f"❌ Status check failed - Status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Status check error: {e}")
            return False
        
        # Test 4: Submit text response
        print("\n4️⃣ Testing text response...")
        try:
            response = await client.post(f"{base_url}/api/interview/{session_id}/respond", json={
                "response_text": "VLOOKUP is used for vertical lookups in Excel tables. It searches the first column of a range and returns a value from a specified column in the same row.",
                "time_taken_seconds": 45,
                "confidence_level": 4
            })
            if response.status_code == 200:
                response_data = response.json()
                if response_data["success"]:
                    evaluation = response_data.get("evaluation", {})
                    score = evaluation.get("score", 0)
                    print(f"✅ Response evaluated - Score: {score}/5.0")
                else:
                    print("❌ Response evaluation failed")
                    return False
            else:
                print(f"❌ Response submission failed - Status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Response submission error: {e}")
            return False
        
        # Test 5: System stats (if available)
        print("\n5️⃣ Testing system stats...")
        try:
            response = await client.get(f"{base_url}/api/system/stats")
            if response.status_code == 200:
                print("✅ System stats retrieved")
            else:
                print(f"⚠️ System stats not available - Status: {response.status_code}")
        except Exception as e:
            print(f"⚠️ System stats error (this is optional): {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Integration test completed successfully!")
    print("✅ All core systems are working properly")
    print("🚀 Ready to build the Streamlit frontend!")
    
    return True

if __name__ == "__main__":
    print("Starting integration test...")
    print("⏳ Make sure the server is running (python main.py)")
    print("⏳ Waiting 3 seconds for you to start the server...")
    
    import time
    time.sleep(3)
    
    asyncio.run(test_integration())