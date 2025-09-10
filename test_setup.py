#!/usr/bin/env python3
"""
Test script to verify the CI/CD Dashboard setup
"""

import requests
import json
import time
from datetime import datetime, timezone

BACKEND_URL = "http://localhost:8001"

def test_health_endpoint():
    """Test the health endpoint"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint is working")
            return True
        else:
            print(f"❌ Health endpoint returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Health endpoint failed: {e}")
        return False

def test_ingest_github():
    """Test GitHub data ingestion"""
    try:
        payload = {
            "pipeline": "test-pipeline",
            "repo": "test-org/test-repo",
            "branch": "main",
            "status": "success",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": 120,
            "url": "https://github.com/test-org/test-repo/actions/runs/123",
            "logs": "Test build completed successfully"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/ingest/github",
            json=payload,
            timeout=5
        )
        
        if response.status_code == 200:
            print("✅ GitHub ingestion is working")
            return True
        else:
            print(f"❌ GitHub ingestion failed with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ GitHub ingestion failed: {e}")
        return False

def test_ingest_jenkins():
    """Test Jenkins data ingestion"""
    try:
        payload = {
            "pipeline": "jenkins-test",
            "repo": "test-org/jenkins-repo",
            "branch": "develop",
            "status": "failure",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": 180,
            "url": "https://jenkins.test.com/job/test/123/",
            "logs": "Test build failed: compilation error"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/ingest/jenkins",
            json=payload,
            timeout=5
        )
        
        if response.status_code == 200:
            print("✅ Jenkins ingestion is working")
            return True
        else:
            print(f"❌ Jenkins ingestion failed with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Jenkins ingestion failed: {e}")
        return False

def test_metrics_endpoint():
    """Test metrics endpoint"""
    try:
        response = requests.get(f"{BACKEND_URL}/metrics/summary", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Metrics endpoint is working")
            print(f"   Success rate: {data.get('success_rate', 0):.1f}%")
            print(f"   Failure rate: {data.get('failure_rate', 0):.1f}%")
            return True
        else:
            print(f"❌ Metrics endpoint failed with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Metrics endpoint failed: {e}")
        return False

def test_builds_endpoint():
    """Test builds endpoint"""
    try:
        response = requests.get(f"{BACKEND_URL}/builds", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Builds endpoint is working ({len(data)} builds found)")
            return True
        else:
            print(f"❌ Builds endpoint failed with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Builds endpoint failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing CI/CD Dashboard Setup")
    print("=" * 40)
    
    tests = [
        test_health_endpoint,
        test_ingest_github,
        test_ingest_jenkins,
        test_metrics_endpoint,
        test_builds_endpoint
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 40)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your CI/CD Dashboard is working correctly.")
        print("\nNext steps:")
        print("1. Open http://localhost:5173 to view the dashboard")
        print("2. Configure webhooks in your CI/CD providers")
        print("3. Set up alerting in your .env file")
    else:
        print("❌ Some tests failed. Please check your setup.")
        print("\nTroubleshooting:")
        print("1. Make sure the backend is running: docker-compose up -d")
        print("2. Check the logs: docker-compose logs backend")
        print("3. Verify the health endpoint: curl http://localhost:8001/health")

if __name__ == "__main__":
    main()
