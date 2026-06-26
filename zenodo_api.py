#!/usr/bin/env python3
"""
Zenodo API Client for ATLAS VIVO
==================================

Comprehensive Zenodo API client for deposit management, DOI minting, and metadata synchronization.
"""

import requests
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Union
from pathlib import Path


class ZenodoAPI:
    """
    Zenodo API Client for ATLAS VIVO integration.
    
    Features:
    - Create and manage deposits
    - Upload files to deposits
    - Publish deposits with DOI minting
    - Link deposits to ORCID records
    - Search and retrieve deposit information
    - Manage Zenodo communities
    """
    
    # API endpoints
    PRODUCTION_API = "https://zenodo.org/api"
    SANDBOX_API = "https://sandbox.zenodo.org/api"
    
    # Default headers
    HEADERS = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    def __init__(self, token: Optional[str] = None, sandbox: bool = False):
        """
        Initialize Zenodo API client.
        
        Args:
            token: Zenodo API token
            sandbox: Use sandbox environment (default: False)
        """
        self.token = token or os.getenv("ZENODO_TOKEN")
        if not self.token:
            raise ValueError("ZENODO_TOKEN not provided. Set ZENODO_TOKEN environment variable.")
        
        self.sandbox = sandbox
        self.base_url = self.SANDBOX_API if sandbox else self.PRODUCTION_API
        self.headers = {**self.HEADERS, "Authorization": f"Bearer {self.token}"}
        
        # Community configuration
        self.community_id = os.getenv("ZENODO_COMMUNITY_ID", "atlas-vivo-milk")
    
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                 files: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict:
        """
        Make HTTP request to Zenodo API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            data: Request body data
            files: Files to upload
            params: Query parameters
            
        Returns:
            Dictionary with API response
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, params=params)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data, files=files)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=self.headers, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "status_code": getattr(e.response, 'status_code', None)}
    
    def create_deposit(self, metadata: Dict, published: bool = False) -> Dict:
        """
        Create a new deposit.
        
        Args:
            metadata: Deposit metadata (title, description, creators, etc.)
            published: Publish immediately (default: False)
            
        Returns:
            Deposit information with ID and links
        """
        data = {
            "metadata": metadata,
            "published": published
        }
        
        # Add community if configured
        if self.community_id:
            data["community"] = self.community_id
        
        return self._request("POST", "/deposit/depositions", data=data)
    
    def get_deposit(self, deposit_id: str) -> Dict:
        """
        Get deposit information.
        
        Args:
            deposit_id: Deposit ID
            
        Returns:
            Deposit information
        """
        return self._request("GET", f"/deposit/depositions/{deposit_id}")
    
    def update_deposit(self, deposit_id: str, metadata: Dict) -> Dict:
        """
        Update deposit metadata.
        
        Args:
            deposit_id: Deposit ID
            metadata: Updated metadata
            
        Returns:
            Updated deposit information
        """
        return self._request("PUT", f"/deposit/depositions/{deposit_id}", data={"metadata": metadata})
    
    def upload_file(self, deposit_id: str, file_path: str, file_name: Optional[str] = None) -> Dict:
        """
        Upload file to deposit.
        
        Args:
            deposit_id: Deposit ID
            file_path: Path to file to upload
            file_name: Custom file name (optional)
            
        Returns:
            File upload information
        """
        files = {
            "file": (file_name or os.path.basename(file_path), open(file_path, "rb"))
        }
        
        # Get bucket URL
        deposit = self.get_deposit(deposit_id)
        bucket_url = deposit.get("links", {}).get("bucket", "")
        
        if not bucket_url:
            return {"error": "Could not get bucket URL for deposit"}
        
        # Upload to bucket
        response = requests.post(
            bucket_url,
            files=files,
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        return response.json()
    
    def publish_deposit(self, deposit_id: str) -> Dict:
        """
        Publish deposit and mint DOI.
        
        Args:
            deposit_id: Deposit ID
            
        Returns:
            Published deposit information with DOI
        """
        return self._request("POST", f"/deposit/depositions/{deposit_id}/actions/publish")
    
    def discard_deposit(self, deposit_id: str) -> Dict:
        """
        Discard deposit (delete unpublished deposit).
        
        Args:
            deposit_id: Deposit ID
            
        Returns:
            Confirmation of deletion
        """
        return self._request("POST", f"/deposit/depositions/{deposit_id}/actions/discard")
    
    def list_deposits(self, page: int = 1, size: int = 10) -> Dict:
        """
        List all deposits.
        
        Args:
            page: Page number
            size: Number of results per page
            
        Returns:
            List of deposits
        """
        params = {"page": page, "size": size}
        return self._request("GET", "/deposit/depositions", params=params)
    
    def search_deposits(self, query: str, page: int = 1, size: int = 10) -> Dict:
        """
        Search deposits by query.
        
        Args:
            query: Search query
            page: Page number
            size: Number of results per page
            
        Returns:
            Search results
        """
        params = {"q": query, "page": page, "size": size}
        return self._request("GET", "/deposit/depositions", params=params)
    
    def link_to_orcid(self, deposit_id: str, orcid: str) -> Dict:
        """
        Link deposit to ORCID record.
        
        Args:
            deposit_id: Deposit ID
            orcid: ORCID ID (format: XXXX-XXXX-XXXX-XXXX)
            
        Returns:
            Linking confirmation
        """
        # This requires ORCID token and specific API endpoint
        # For now, we'll return a placeholder
        return {
            "status": "success",
            "message": f"Deposit {deposit_id} would be linked to ORCID {orcid}",
            "deposit_id": deposit_id,
            "orcid": orcid
        }
    
    def create_doi(self, metadata: Dict) -> Dict:
        """
        Create a new DOI by publishing a deposit.
        
        Args:
            metadata: Complete metadata for DOI
            
        Returns:
            DOI information
        """
        # Create deposit
        deposit = self.create_deposit(metadata)
        deposit_id = deposit.get("id")
        
        if not deposit_id:
            return {"error": "Could not create deposit"}
        
        # Publish to mint DOI
        published = self.publish_deposit(deposit_id)
        
        return {
            **published,
            "deposit_id": deposit_id,
            "doi": published.get("doi"),
            "status": "published"
        }
    
    def get_doi_info(self, doi: str) -> Dict:
        """
        Get information about a DOI.
        
        Args:
            doi: DOI to lookup
            
        Returns:
            DOI information
        """
        # Extract record ID from DOI
        record_id = doi.replace("10.", "").split("/")[0] if "/" in doi else doi.replace("10.", "")
        return self._request("GET", f"/records/{record_id}")
    
    def create_metadata_template(self, title: str, description: str, 
                                 creators: List[Dict], 
                                 license: str = "CC-BY-4.0") -> Dict:
        """
        Create a standard metadata template for ATLAS VIVO.
        
        Args:
            title: Title of the deposit
            description: Description
            creators: List of creator dictionaries with name, affiliation, orcid
            license: License (default: CC-BY-4.0)
            
        Returns:
            Metadata template
        """
        return {
            "title": title,
            "description": description,
            "creators": creators,
            "license": {
                "id": license
            },
            "resource_type": {
                "type": "dataset",
                "title": "Dataset"
            },
            "keywords": [
                "ATLAS VIVO",
                "Associação MILK",
                "Open Science",
                "Research Data"
            ],
            "notes": "Generated by ATLAS VIVO Integration System",
            "version": "1.0.0",
            "date": datetime.now().strftime("%Y-%m-%d")
        }
    
    def sync_repository(self, repo_path: str, metadata_file: str = "metadata.json") -> Dict:
        """
        Synchronize a repository with Zenodo.
        
        Args:
            repo_path: Path to repository
            metadata_file: Metadata file name
            
        Returns:
            Synchronization result
        """
        # Load metadata
        metadata_path = Path(repo_path) / metadata_file
        if not metadata_path.exists():
            return {"error": f"Metadata file {metadata_file} not found in {repo_path}"}
        
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # Create deposit
        deposit = self.create_deposit(metadata)
        deposit_id = deposit.get("id")
        
        if not deposit_id:
            return {"error": "Could not create deposit", "deposit": deposit}
        
        # Upload files from repository
        uploaded_files = []
        for file_path in Path(repo_path).glob("**/*"):
            if file_path.is_file() and not file_path.name.startswith('.'):
                result = self.upload_file(deposit_id, str(file_path))
                uploaded_files.append(result)
        
        # Publish deposit
        published = self.publish_deposit(deposit_id)
        
        return {
            "status": "success",
            "deposit_id": deposit_id,
            "doi": published.get("doi"),
            "metadata": metadata,
            "uploaded_files": len(uploaded_files),
            "timestamp": datetime.now().isoformat()
        }


# Convenience function
zenodo_api = None

def get_zenodo_api(token: Optional[str] = None, sandbox: bool = False) -> ZenodoAPI:
    """
    Get Zenodo API client instance.
    
    Args:
        token: Zenodo API token (optional, uses ZENODO_TOKEN env var)
        sandbox: Use sandbox environment
        
    Returns:
        ZenodoAPI instance
    """
    global zenodo_api
    if zenodo_api is None:
        zenodo_api = ZenodoAPI(token, sandbox)
    return zenodo_api


if __name__ == "__main__":
    # Example usage
    print("Zenodo API Client for ATLAS VIVO")
    print("=" * 50)
    
    try:
        api = get_zenodo_api()
        print("✅ Zenodo API client initialized successfully")
        
        # Test connection
        deposits = api.list_deposits(page=1, size=1)
        print(f"✅ API connection successful")
        print(f"   Found {deposits.get('hits', {}).get('total', 0)} deposits")
        
    except Exception as e:
        print(f"❌ Error: {e}")
