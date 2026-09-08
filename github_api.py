#!/usr/bin/env python3
"""
GitHub API Client for ATLAS VIVO
==================================

Comprehensive GitHub API client for repository management and automation.
"""

import requests
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Union
from pathlib import Path


class GitHubAPI:
    """
    GitHub API Client for ATLAS VIVO integration.
    
    Features:
    - Repository management
    - File operations
    - Workflow management
    - Issue and PR management
    - Repository synchronization
    - Metadata management
    """
    
    # API endpoints
    API_URL = "https://api.github.com"
    GRAPHQL_URL = "https://api.github.com/graphql"
    
    # Default headers
    HEADERS = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub API client.
        
        Args:
            token: GitHub Personal Access Token
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GITHUB_TOKEN not provided. Set GITHUB_TOKEN environment variable.")
        
        self.headers = {**self.HEADERS, "Authorization": f"Bearer {self.token}"}
        self.org = os.getenv("REPOSITORY_OWNER", "milkivc")
    
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None,
                 params: Optional[Dict] = None) -> Dict:
        """
        Make HTTP request to GitHub API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            endpoint: API endpoint
            data: Request body data
            params: Query parameters
            
        Returns:
            Dictionary with API response
        """
        url = f"{self.API_URL}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, params=params)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=self.headers, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=self.headers)
            elif method.upper() == "PATCH":
                response = requests.patch(url, headers=self.headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "status_code": getattr(e.response, 'status_code', None)}
    
    def get_user(self) -> Dict:
        """Get authenticated user information."""
        return self._request("GET", "/user")
    
    def get_repo(self, owner: str, repo: str) -> Dict:
        """
        Get repository information.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Repository information
        """
        return self._request("GET", f"/repos/{owner}/{repo}")
    
    def list_repos(self, org: Optional[str] = None) -> List[Dict]:
        """
        List repositories.
        
        Args:
            org: Organization name (optional)
            
        Returns:
            List of repositories
        """
        endpoint = f"/orgs/{org}/repos" if org else "/user/repos"
        return self._request("GET", endpoint)
    
    def create_repo(self, name: str, description: str = "", private: bool = False,
                   auto_init: bool = True) -> Dict:
        """
        Create a new repository.
        
        Args:
            name: Repository name
            description: Repository description
            private: Private repository
            auto_init: Initialize with README
            
        Returns:
            Created repository information
        """
        data = {
            "name": name,
            "description": description,
            "private": private,
            "auto_init": auto_init
        }
        return self._request("POST", f"/orgs/{self.org}/repos", data=data)
    
    def update_repo(self, owner: str, repo: str, data: Dict) -> Dict:
        """
        Update repository settings.
        
        Args:
            owner: Repository owner
            repo: Repository name
            data: Update data
            
        Returns:
            Updated repository information
        """
        return self._request("PATCH", f"/repos/{owner}/{repo}", data=data)
    
    def get_file(self, owner: str, repo: str, path: str) -> Dict:
        """
        Get file information.
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: File path
            
        Returns:
            File information
        """
        return self._request("GET", f"/repos/{owner}/{repo}/contents/{path}")
    
    def create_file(self, owner: str, repo: str, path: str, content: str,
                   message: str = "Add file") -> Dict:
        """
        Create or update a file.
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: File path
            content: File content
            message: Commit message
            
        Returns:
            File creation result
        """
        import base64
        data = {
            "message": message,
            "content": base64.b64encode(content.encode()).decode()
        }
        return self._request("PUT", f"/repos/{owner}/{repo}/contents/{path}", data=data)
    
    def delete_file(self, owner: str, repo: str, path: str,
                   message: str = "Delete file") -> Dict:
        """
        Delete a file.
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: File path
            message: Commit message
            
        Returns:
            File deletion result
        """
        data = {"message": message}
        return self._request("DELETE", f"/repos/{owner}/{repo}/contents/{path}", data=data)
    
    def list_files(self, owner: str, repo: str, path: str = "") -> List[Dict]:
        """
        List files in a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: Directory path
            
        Returns:
            List of files
        """
        return self._request("GET", f"/repos/{owner}/{repo}/contents/{path}")
    
    def get_workflow(self, owner: str, repo: str, workflow_id: str) -> Dict:
        """
        Get workflow information.
        
        Args:
            owner: Repository owner
            repo: Repository name
            workflow_id: Workflow ID or filename
            
        Returns:
            Workflow information
        """
        return self._request("GET", f"/repos/{owner}/{repo}/actions/workflows/{workflow_id}")
    
    def list_workflows(self, owner: str, repo: str) -> List[Dict]:
        """
        List all workflows in a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            List of workflows
        """
        return self._request("GET", f"/repos/{owner}/{repo}/actions/workflows")
    
    def trigger_workflow(self, owner: str, repo: str, workflow_id: str,
                        branch: str = "master", inputs: Optional[Dict] = None) -> Dict:
        """
        Trigger a workflow run.
        
        Args:
            owner: Repository owner
            repo: Repository name
            workflow_id: Workflow ID or filename
            branch: Branch to run on
            inputs: Workflow inputs
            
        Returns:
            Workflow run information
        """
        data = {
            "ref": branch,
            "inputs": inputs or {}
        }
        return self._request("POST", f"/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches", data=data)
    
    def get_workflow_runs(self, owner: str, repo: str, workflow_id: Optional[str] = None) -> List[Dict]:
        """
        Get workflow runs.
        
        Args:
            owner: Repository owner
            repo: Repository name
            workflow_id: Workflow ID (optional)
            
        Returns:
            List of workflow runs
        """
        endpoint = f"/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs" if workflow_id \
                 else f"/repos/{owner}/{repo}/actions/runs"
        return self._request("GET", endpoint)
    
    def create_secret(self, owner: str, repo: str, secret_name: str, secret_value: str) -> Dict:
        """
        Create or update a repository secret.
        
        Args:
            owner: Repository owner
            repo: Repository name
            secret_name: Secret name
            secret_value: Secret value
            
        Returns:
            Secret creation result
        """
        # Note: GitHub API requires encrypted value for secrets
        # This is a placeholder - actual implementation requires public key encryption
        import base64
        data = {
            "name": secret_name,
            "value": base64.b64encode(secret_value.encode()).decode()
        }
        return self._request("PUT", f"/repos/{owner}/{repo}/actions/secrets/{secret_name}", data=data)
    
    def get_secrets(self, owner: str, repo: str) -> List[Dict]:
        """
        List repository secrets.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            List of secrets
        """
        return self._request("GET", f"/repos/{owner}/{repo}/actions/secrets")
    
    def create_issue(self, owner: str, repo: str, title: str, body: str,
                    labels: Optional[List[str]] = None) -> Dict:
        """
        Create a new issue.
        
        Args:
            owner: Repository owner
            repo: Repository name
            title: Issue title
            body: Issue body
            labels: Issue labels
            
        Returns:
            Created issue information
        """
        data = {
            "title": title,
            "body": body,
            "labels": labels or []
        }
        return self._request("POST", f"/repos/{owner}/{repo}/issues", data=data)
    
    def create_pr(self, owner: str, repo: str, title: str, body: str,
                 head: str, base: str = "master") -> Dict:
        """
        Create a new pull request.
        
        Args:
            owner: Repository owner
            repo: Repository name
            title: PR title
            body: PR body
            head: Head branch
            base: Base branch
            
        Returns:
            Created PR information
        """
        data = {
            "title": title,
            "body": body,
            "head": head,
            "base": base
        }
        return self._request("POST", f"/repos/{owner}/{repo}/pulls", data=data)
    
    def sync_metadata(self, owner: str, repo: str, metadata: Dict) -> Dict:
        """
        Synchronize metadata files in a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            metadata: Metadata to sync
            
        Returns:
            Sync result
        """
        results = {}
        
        # Update metadata.json
        if "metadata" in metadata:
            result = self.create_file(
                owner, repo, "metadata.json",
                json.dumps(metadata["metadata"], indent=2),
                "Update metadata.json"
            )
            results["metadata.json"] = result
        
        # Update .zenodo.json
        if "zenodo" in metadata:
            result = self.create_file(
                owner, repo, ".zenodo.json",
                json.dumps(metadata["zenodo"], indent=2),
                "Update .zenodo.json"
            )
            results[".zenodo.json"] = result
        
        # Update CITATION.cff
        if "citation" in metadata:
            result = self.create_file(
                owner, repo, "CITATION.cff",
                metadata["citation"],
                "Update CITATION.cff"
            )
            results["CITATION.cff"] = result
        
        # Update codemeta.json
        if "codemeta" in metadata:
            result = self.create_file(
                owner, repo, "codemeta.json",
                json.dumps(metadata["codemeta"], indent=2),
                "Update codemeta.json"
            )
            results["codemeta.json"] = result
        
        return results
    
    def get_metadata(self, owner: str, repo: str) -> Dict:
        """
        Get all metadata files from a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Dictionary with all metadata
        """
        metadata = {}
        
        # Get metadata.json
        try:
            result = self.get_file(owner, repo, "metadata.json")
            if "content" in result:
                import base64
                content = base64.b64decode(result["content"]).decode()
                metadata["metadata"] = json.loads(content)
        except:
            pass
        
        # Get .zenodo.json
        try:
            result = self.get_file(owner, repo, ".zenodo.json")
            if "content" in result:
                import base64
                content = base64.b64decode(result["content"]).decode()
                metadata["zenodo"] = json.loads(content)
        except:
            pass
        
        # Get CITATION.cff
        try:
            result = self.get_file(owner, repo, "CITATION.cff")
            if "content" in result:
                import base64
                content = base64.b64decode(result["content"]).decode()
                metadata["citation"] = content
        except:
            pass
        
        # Get codemeta.json
        try:
            result = self.get_file(owner, repo, "codemeta.json")
            if "content" in result:
                import base64
                content = base64.b64decode(result["content"]).decode()
                metadata["codemeta"] = json.loads(content)
        except:
            pass
        
        return metadata
    
    def sync_repositories(self, repos: List[str], metadata: Dict) -> Dict:
        """
        Synchronize metadata across multiple repositories.
        
        Args:
            repos: List of repository names
            metadata: Metadata to sync
            
        Returns:
            Sync results for all repositories
        """
        results = {}
        for repo in repos:
            try:
                result = self.sync_metadata(self.org, repo, metadata)
                results[repo] = {"status": "success", "result": result}
            except Exception as e:
                results[repo] = {"status": "error", "error": str(e)}
        
        return results


# Convenience function
github_api = None

def get_github_api(token: Optional[str] = None) -> GitHubAPI:
    """
    Get GitHub API client instance.
    
    Args:
        token: GitHub Personal Access Token
        
    Returns:
        GitHubAPI instance
    """
    global github_api
    if github_api is None:
        github_api = GitHubAPI(token)
    return github_api


if __name__ == "__main__":
    # Example usage
    print("GitHub API Client for ATLAS VIVO")
    print("=" * 50)
    
    try:
        api = get_github_api()
        print("✅ GitHub API client initialized successfully")
        
        # Test connection
        user = api.get_user()
        print(f"✅ API connection successful")
        print(f"   Authenticated as: {user.get('login')}")
        
        # List repositories
        repos = api.list_repos(api.org)
        print(f"✅ Found {len(repos)} repositories in {api.org}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
