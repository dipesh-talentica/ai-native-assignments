#!/usr/bin/env python3
"""
Jenkins Data Collector

This script polls Jenkins API to collect build data
and sends it to the CI/CD Dashboard backend.
"""

import os
import sys
import time
import requests
import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
from urllib.parse import urljoin

# Add parent directory to path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class JenkinsCollector:
    def __init__(self, jenkins_url: str, username: str, api_token: str, backend_url: str = "http://localhost:8001"):
        self.jenkins_url = jenkins_url.rstrip('/')
        self.username = username
        self.api_token = api_token
        self.backend_url = backend_url
        self.session = requests.Session()
        self.session.auth = (username, api_token)
        self.session.headers.update({
            "User-Agent": "CI-CD-Dashboard-Collector/1.0"
        })
    
    def get_jobs(self) -> List[Dict]:
        """Get all jobs from Jenkins"""
        url = urljoin(self.jenkins_url, "/api/json")
        params = {
            "tree": "jobs[name,url,lastBuild[number,url,result,timestamp,duration,fullDisplayName]]"
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("jobs", [])
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching jobs: {e}")
            return []
    
    def get_job_builds(self, job_name: str, since: Optional[datetime] = None) -> List[Dict]:
        """Get builds for a specific job"""
        if since is None:
            since = datetime.now(timezone.utc) - timedelta(hours=24)
        
        since_timestamp = int(since.timestamp() * 1000)  # Jenkins uses milliseconds
        
        url = urljoin(self.jenkins_url, f"/job/{job_name}/api/json")
        params = {
            "tree": "builds[number,url,result,timestamp,duration,fullDisplayName,changeSet[items[msg]]]",
            "since": since_timestamp
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("builds", [])
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching builds for job {job_name}: {e}")
            return []
    
    def transform_build(self, build: Dict, job_name: str) -> Dict:
        """Transform Jenkins build to dashboard format"""
        # Extract repository info from changeSet if available
        repo_info = self._extract_repo_info(build)
        
        return {
            "pipeline": job_name,
            "repo": repo_info.get("repo", "unknown"),
            "branch": repo_info.get("branch", "main"),
            "status": self._map_result_to_status(build.get("result")),
            "started_at": self._timestamp_to_iso(build.get("timestamp")),
            "completed_at": self._timestamp_to_iso(build.get("timestamp") + build.get("duration", 0)),
            "duration_seconds": self._duration_to_seconds(build.get("duration")),
            "url": build.get("url"),
            "logs": f"Jenkins build #{build.get('number', 'unknown')} - {build.get('result', 'unknown')}"
        }
    
    def _extract_repo_info(self, build: Dict) -> Dict:
        """Extract repository information from build changeset"""
        changeset = build.get("changeSet", {})
        items = changeset.get("items", [])
        
        if items:
            # Try to extract repo info from commit messages or other metadata
            # This is a simplified approach - in practice, you might need more sophisticated parsing
            first_item = items[0]
            msg = first_item.get("msg", "")
            
            # Simple heuristic: look for common repo patterns in commit messages
            if "github.com" in msg or "gitlab.com" in msg:
                # Extract repo from commit message (this is very basic)
                return {"repo": "extracted-from-commit", "branch": "main"}
        
        return {"repo": "unknown", "branch": "main"}
    
    def _map_result_to_status(self, result: Optional[str]) -> str:
        """Map Jenkins result to dashboard status"""
        if result == "SUCCESS":
            return "success"
        elif result == "FAILURE":
            return "failure"
        elif result == "ABORTED":
            return "cancelled"
        else:
            return "in_progress"
    
    def _timestamp_to_iso(self, timestamp: Optional[int]) -> str:
        """Convert Jenkins timestamp to ISO format"""
        if not timestamp:
            return datetime.now(timezone.utc).isoformat()
        
        # Jenkins timestamps are in milliseconds
        dt = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
        return dt.isoformat()
    
    def _duration_to_seconds(self, duration: Optional[int]) -> Optional[float]:
        """Convert Jenkins duration to seconds"""
        if duration is None:
            return None
        return duration / 1000.0  # Jenkins duration is in milliseconds
    
    def send_to_dashboard(self, data: Dict) -> bool:
        """Send data to the dashboard backend"""
        try:
            response = requests.post(
                f"{self.backend_url}/ingest/jenkins",
                json=data,
                timeout=10
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error sending data to dashboard: {e}")
            return False
    
    def collect_jenkins_data(self, hours_back: int = 24):
        """Collect data for all jobs in Jenkins"""
        print(f"Collecting Jenkins build data from: {self.jenkins_url}")
        
        jobs = self.get_jobs()
        print(f"Found {len(jobs)} jobs")
        
        since = datetime.now(timezone.utc) - timedelta(hours=hours_back)
        total_builds = 0
        
        for job in jobs:
            job_name = job["name"]
            print(f"Processing job: {job_name}")
            
            builds = self.get_job_builds(job_name, since)
            print(f"  Found {len(builds)} builds")
            
            for build in builds:
                # Only process completed builds
                if build.get("result") in ["SUCCESS", "FAILURE", "ABORTED"]:
                    data = self.transform_build(build, job_name)
                    
                    if self.send_to_dashboard(data):
                        total_builds += 1
                        print(f"  ✓ Sent build #{build.get('number')} ({data['status']})")
                    else:
                        print(f"  ✗ Failed to send build #{build.get('number')}")
        
        print(f"Successfully collected {total_builds} builds")
        return total_builds

def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Jenkins Data Collector")
    parser.add_argument("--jenkins-url", required=True, help="Jenkins server URL")
    parser.add_argument("--username", required=True, help="Jenkins username")
    parser.add_argument("--api-token", required=True, help="Jenkins API token")
    parser.add_argument("--backend", default="http://localhost:8001", help="Dashboard backend URL")
    parser.add_argument("--hours", type=int, default=24, help="Hours back to collect data")
    parser.add_argument("--interval", type=int, help="Polling interval in seconds (for continuous mode)")
    
    args = parser.parse_args()
    
    collector = JenkinsCollector(args.jenkins_url, args.username, args.api_token, args.backend)
    
    if args.interval:
        print(f"Starting continuous collection (every {args.interval} seconds)")
        while True:
            try:
                collector.collect_jenkins_data(args.hours)
                print(f"Waiting {args.interval} seconds before next collection...")
                time.sleep(args.interval)
            except KeyboardInterrupt:
                print("Collection stopped by user")
                break
            except Exception as e:
                print(f"Error during collection: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    else:
        collector.collect_jenkins_data(args.hours)

if __name__ == "__main__":
    main()
