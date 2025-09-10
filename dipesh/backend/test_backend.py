#!/usr/bin/env python3
"""
Backend Test Suite

Tests for the CI/CD Dashboard backend API endpoints.
"""

import pytest
import requests
import json
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import app

client = TestClient(app)

class TestBackendAPI:
    """Test cases for the backend API"""
    
    def test_health_endpoint(self):
        """Test the health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["service"] == "ci-cd-dashboard-backend"
    
    def test_github_ingest_success(self):
        """Test GitHub data ingestion with success status"""
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
        
        response = client.post("/ingest/github", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "github"
        assert data["pipeline"] == "test-pipeline"
        assert data["status"] == "success"
        assert "id" in data
    
    def test_jenkins_ingest_failure(self):
        """Test Jenkins data ingestion with failure status"""
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
        
        response = client.post("/ingest/jenkins", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "jenkins"
        assert data["pipeline"] == "jenkins-test"
        assert data["status"] == "failure"
        assert "id" in data
    
    def test_ingest_invalid_status(self):
        """Test ingestion with invalid status"""
        payload = {
            "pipeline": "test-pipeline",
            "repo": "test-org/test-repo",
            "branch": "main",
            "status": "invalid-status",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": 120
        }
        
        response = client.post("/ingest/github", json=payload)
        assert response.status_code == 422  # Validation error
    
    def test_ingest_missing_required_fields(self):
        """Test ingestion with missing required fields"""
        payload = {
            "pipeline": "test-pipeline",
            "repo": "test-org/test-repo",
            "branch": "main",
            "status": "success"
            # Missing started_at
        }
        
        response = client.post("/ingest/github", json=payload)
        assert response.status_code == 422  # Validation error
    
    def test_builds_endpoint(self):
        """Test the builds listing endpoint"""
        response = client.get("/builds")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_builds_endpoint_with_limit(self):
        """Test the builds endpoint with limit parameter"""
        response = client.get("/builds?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10
    
    def test_metrics_summary_endpoint(self):
        """Test the metrics summary endpoint"""
        response = client.get("/metrics/summary")
        assert response.status_code == 200
        data = response.json()
        assert "window" in data
        assert "success_rate" in data
        assert "failure_rate" in data
        assert "avg_build_time" in data
        assert "last_status_by_pipeline" in data
        assert isinstance(data["success_rate"], (int, float))
        assert isinstance(data["failure_rate"], (int, float))
    
    def test_metrics_summary_with_window(self):
        """Test metrics summary with different time windows"""
        for window in ["1h", "24h", "7d", "30d"]:
            response = client.get(f"/metrics/summary?window={window}")
            assert response.status_code == 200
            data = response.json()
            assert data["window"] == window
    
    def test_latest_build_endpoint(self):
        """Test the latest build endpoint"""
        response = client.get("/builds/latest")
        assert response.status_code == 200
        # Response can be null if no builds exist
        data = response.json()
        if data is not None:
            assert "id" in data
            assert "provider" in data
            assert "pipeline" in data
    
    def test_latest_build_with_pipeline_filter(self):
        """Test latest build endpoint with pipeline filter"""
        response = client.get("/builds/latest?pipeline=test-pipeline")
        assert response.status_code == 200
        # Response can be null if no builds exist for that pipeline
        data = response.json()
        if data is not None:
            assert data["pipeline"] == "test-pipeline"
    
    def test_github_webhook_endpoint(self):
        """Test GitHub webhook endpoint"""
        payload = {
            "action": "completed",
            "workflow_run": {
                "name": "CI Pipeline",
                "conclusion": "success",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "html_url": "https://github.com/test/repo/actions/runs/123",
                "run_number": 123
            },
            "repository": {
                "full_name": "test-org/test-repo"
            }
        }
        
        response = client.post("/webhook/github", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_jenkins_webhook_endpoint(self):
        """Test Jenkins webhook endpoint"""
        payload = {
            "workflow_run": {
                "name": "Jenkins Build",
                "conclusion": "failure",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "html_url": "https://jenkins.test.com/job/test/123/",
                "run_number": 123
            },
            "repository": {
                "full_name": "test-org/jenkins-repo"
            }
        }
        
        response = client.post("/webhook/jenkins", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_github_webhook_ignored_action(self):
        """Test GitHub webhook with non-completed action"""
        payload = {
            "action": "requested",  # Not completed
            "workflow_run": {
                "name": "CI Pipeline",
                "conclusion": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "html_url": "https://github.com/test/repo/actions/runs/123",
                "run_number": 123
            },
            "repository": {
                "full_name": "test-org/test-repo"
            }
        }
        
        response = client.post("/webhook/github", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ignored"

def test_database_connection():
    """Test database connection and table creation"""
    from database import engine, Base
    from models import Build
    
    # This should not raise an exception
    Base.metadata.create_all(bind=engine)
    
    # Test that we can create a session
    from database import SessionLocal
    db = SessionLocal()
    try:
        # Simple query to test connection
        result = db.execute("SELECT 1").scalar()
        assert result == 1
    finally:
        db.close()

def test_models():
    """Test SQLAlchemy models"""
    from models import Build
    from datetime import datetime, timezone
    
    # Test model creation
    build = Build(
        provider="github",
        pipeline="test-pipeline",
        repo="test-org/test-repo",
        branch="main",
        status="success",
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        duration_seconds=120.0,
        url="https://github.com/test/repo/actions/runs/123",
        logs="Test build"
    )
    
    assert build.provider == "github"
    assert build.pipeline == "test-pipeline"
    assert build.status == "success"
    assert build.duration_seconds == 120.0

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
