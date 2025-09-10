#!/usr/bin/env python3
"""
GitHub Actions Data Collector

This script polls GitHub Actions API to collect workflow run data
and sends it to the CI/CD Dashboard backend.
"""

import os
import sys
import time
import requests
import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional

# Add parent directory to path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class GitHubCollector:
    def __init__(self, token: str, backend_url: str = "http://localhost:8001"):
        self.token = token
        self.backend_url = backend_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "CI-CD-Dashboard-Collector/1.0"
        })
    
    def get_repositories(self, org: str) -> List[Dict]:
        """Get all repositories for an organization"""
        repos = []
        page = 1
        per_page = 100
        
        while True:
            url = f"https://api.github.com/orgs/{org}/repos"
            params = {
                "page": page,
                "per_page": per_page,
                "sort": "updated",
                "direction": "desc"
            }
            
            try:
                response = self.session.get(url, params=params)
                response.raise_for_status()
                page_repos = response.json()
                
                if not page_repos:
                    break
                    
                repos.extend(page_repos)
                page += 1
                
            except requests.exceptions.RequestException as e:
                print(f"Error fetching repositories: {e}")
                break
        
        return repos
    
    def get_workflow_runs(self, owner: str, repo: str, since: Optional[datetime] = None) -> List[Dict]:
        """Get workflow runs for a repository"""
        if since is None:
            since = datetime.now(timezone.utc) - timedelta(hours=24)
        
        url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs"
        params = {
            "per_page": 100,
            "created": f">{since.isoformat()}"
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("workflow_runs", [])
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching workflow runs for {owner}/{repo}: {e}")
            return []
    
    def transform_workflow_run(self, run: Dict, repo_name: str) -> Dict:
        """Transform GitHub workflow run to dashboard format"""
        return {
            "pipeline": run.get("name", "unknown"),
            "repo": repo_name,
            "branch": run.get("head_branch", "main"),
            "status": self._map_conclusion_to_status(run.get("conclusion")),
            "started_at": run.get("created_at"),
            "completed_at": run.get("updated_at"),
            "duration_seconds": self._calculate_duration(run),
            "url": run.get("html_url"),
            "logs": f"GitHub Actions run #{run.get('run_number', 'unknown')} - {run.get('conclusion', 'unknown')}"
        }
    
    def _map_conclusion_to_status(self, conclusion: Optional[str]) -> str:
        """Map GitHub conclusion to dashboard status"""
        if conclusion == "success":
            return "success"
        elif conclusion == "failure":
            return "failure"
        elif conclusion == "cancelled":
            return "cancelled"
        else:
            return "in_progress"
    
    def _calculate_duration(self, run: Dict) -> Optional[float]:
        """Calculate duration from workflow run data"""
        created_at = run.get("created_at")
        updated_at = run.get("updated_at")
        
        if not created_at or not updated_at:
            return None
        
        try:
            start = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            end = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            return (end - start).total_seconds()
        except (ValueError, TypeError):
            return None
    
    def send_to_dashboard(self, data: Dict) -> bool:
        """Send data to the dashboard backend"""
        try:
            response = requests.post(
                f"{self.backend_url}/ingest/github",
                json=data,
                timeout=10
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error sending data to dashboard: {e}")
            return False
    
    def collect_organization_data(self, org: str, hours_back: int = 24):
        """Collect data for all repositories in an organization"""
        print(f"Collecting GitHub Actions data for organization: {org}")
        
        repos = self.get_repositories(org)
        print(f"Found {len(repos)} repositories")
        
        since = datetime.now(timezone.utc) - timedelta(hours=hours_back)
        total_runs = 0
        
        for repo in repos:
            repo_name = repo["full_name"]
            owner = repo["owner"]["login"]
            repo_name_only = repo["name"]
            
            print(f"Processing repository: {repo_name}")
            
            runs = self.get_workflow_runs(owner, repo_name_only, since)
            print(f"  Found {len(runs)} workflow runs")
            
            for run in runs:
                # Only process completed runs
                if run.get("conclusion") in ["success", "failure", "cancelled"]:
                    data = self.transform_workflow_run(run, repo_name)
                    
                    if self.send_to_dashboard(data):
                        total_runs += 1
                        print(f"  ✓ Sent run #{run.get('run_number')} ({data['status']})")
                    else:
                        print(f"  ✗ Failed to send run #{run.get('run_number')}")
        
        print(f"Successfully collected {total_runs} workflow runs")
        return total_runs

def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="GitHub Actions Data Collector")
    parser.add_argument("--token", required=True, help="GitHub personal access token")
    parser.add_argument("--org", required=True, help="GitHub organization name")
    parser.add_argument("--backend", default="http://localhost:8001", help="Dashboard backend URL")
    parser.add_argument("--hours", type=int, default=24, help="Hours back to collect data")
    parser.add_argument("--interval", type=int, help="Polling interval in seconds (for continuous mode)")
    
    args = parser.parse_args()
    
    collector = GitHubCollector(args.token, args.backend)
    
    if args.interval:
        print(f"Starting continuous collection (every {args.interval} seconds)")
        while True:
            try:
                collector.collect_organization_data(args.org, args.hours)
                print(f"Waiting {args.interval} seconds before next collection...")
                time.sleep(args.interval)
            except KeyboardInterrupt:
                print("Collection stopped by user")
                break
            except Exception as e:
                print(f"Error during collection: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    else:
        collector.collect_organization_data(args.org, args.hours)

if __name__ == "__main__":
    main()
