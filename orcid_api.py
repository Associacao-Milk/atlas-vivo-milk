#!/usr/bin/env python3
"""
ORCID API Client for ATLAS VIVO
==================================

Comprehensive ORCID API client for researcher identification and work linking.
"""

import requests
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Union
from urllib.parse import urlencode


class ORCIDAPI:
    """
    ORCID API Client for ATLAS VIVO integration.
    
    Features:
    - Authenticate with ORCID using OAuth2
    - Get researcher information
    - Add works to ORCID records
    - Update researcher profiles
    - Search ORCID records
    - Link works to multiple ORCIDs
    """
    
    # API endpoints
    PRODUCTION_API = "https://api.orcid.org/v3.0"
    SANDBOX_API = "https://sandbox.orcid.org/v3.0"
    AUTH_URL = "https://orcid.org/oauth/token"
    SANDBOX_AUTH_URL = "https://sandbox.orcid.org/oauth/token"
    
    # Default headers
    HEADERS = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    def __init__(self, client_id: Optional[str] = None, 
                 client_secret: Optional[str] = None, 
                 token: Optional[str] = None, 
                 sandbox: bool = False):
        """
        Initialize ORCID API client.
        
        Args:
            client_id: ORCID Client ID
            client_secret: ORCID Client Secret
            token: ORCID Access Token (optional)
            sandbox: Use sandbox environment (default: False)
        """
        self.client_id = client_id or os.getenv("ORCID_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("ORCID_CLIENT_SECRET")
        self.token = token or os.getenv("ORCID_TOKEN")
        self.sandbox = sandbox
        
        if not self.client_id or not self.client_secret:
            raise ValueError("ORCID_CLIENT_ID and ORCID_CLIENT_SECRET are required")
        
        self.base_url = self.SANDBOX_API if sandbox else self.PRODUCTION_API
        self.auth_url = self.SANDBOX_AUTH_URL if sandbox else self.AUTH_URL
        self.headers = {**self.HEADERS}
        
        # Authenticate if token not provided
        if not self.token:
            self._authenticate()
        else:
            self.headers["Authorization"] = f"Bearer {self.token}"
    
    def _authenticate(self) -> None:
        """Authenticate with ORCID using client credentials."""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
            "scope": "/read-limited /activities/update /person/update"
        }
        
        try:
            response = requests.post(
                self.auth_url,
                data=urlencode(data),
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()
            result = response.json()
            self.token = result.get("access_token")
            self.headers["Authorization"] = f"Bearer {self.token}"
            
        except requests.exceptions.RequestException as e:
            raise ValueError(f"ORCID authentication failed: {e}")
    
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None,
                 params: Optional[Dict] = None) -> Dict:
        """
        Make HTTP request to ORCID API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            data: Request body data
            params: Query parameters
            
        Returns:
            Dictionary with API response
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, params=params)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data)
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
    
    def get_researcher(self, orcid: str) -> Dict:
        """
        Get researcher information.
        
        Args:
            orcid: ORCID ID (format: XXXX-XXXX-XXXX-XXXX)
            
        Returns:
            Researcher information
        """
        return self._request("GET", f"/{orcid}")
    
    def get_researcher_works(self, orcid: str) -> Dict:
        """
        Get researcher's works.
        
        Args:
            orcid: ORCID ID
            
        Returns:
            List of works
        """
        return self._request("GET", f"/{orcid}/works")
    
    def get_work(self, orcid: str, work_id: str) -> Dict:
        """
        Get specific work information.
        
        Args:
            orcid: ORCID ID
            work_id: Work ID
            
        Returns:
            Work information
        """
        return self._request("GET", f"/{orcid}/works/{work_id}")
    
    def add_work(self, orcid: str, work_data: Dict) -> Dict:
        """
        Add a work to researcher's ORCID record.
        
        Args:
            orcid: ORCID ID
            work_data: Work data (title, type, URL, etc.)
            
        Returns:
            Created work information
        """
        return self._request("POST", f"/{orcid}/works", data=work_data)
    
    def update_work(self, orcid: str, work_id: str, work_data: Dict) -> Dict:
        """
        Update a work in researcher's ORCID record.
        
        Args:
            orcid: ORCID ID
            work_id: Work ID
            work_data: Updated work data
            
        Returns:
            Updated work information
        """
        return self._request("PUT", f"/{orcid}/works/{work_id}", data=work_data)
    
    def delete_work(self, orcid: str, work_id: str) -> Dict:
        """
        Delete a work from researcher's ORCID record.
        
        Args:
            orcid: ORCID ID
            work_id: Work ID
            
        Returns:
            Deletion confirmation
        """
        return self._request("DELETE", f"/{orcid}/works/{work_id}")
    
    def search_researchers(self, query: str) -> Dict:
        """
        Search for researchers.
        
        Args:
            query: Search query
            
        Returns:
            Search results
        """
        params = {"q": query}
        return self._request("GET", "/search", params=params)
    
    def get_affiliations(self, orcid: str) -> Dict:
        """
        Get researcher's affiliations.
        
        Args:
            orcid: ORCID ID
            
        Returns:
            List of affiliations
        """
        return self._request("GET", f"/{orcid}/person")
    
    def add_affiliation(self, orcid: str, affiliation_data: Dict) -> Dict:
        """
        Add an affiliation to researcher's ORCID record.
        
        Args:
            orcid: ORCID ID
            affiliation_data: Affiliation data
            
        Returns:
            Created affiliation information
        """
        return self._request("POST", f"/{orcid}/person", data=affiliation_data)
    
    def create_work_payload(self, title: str, doi: str, url: str, 
                           work_type: str = "dataset", 
                           publication_date: Optional[str] = None) -> Dict:
        """
        Create a standard work payload for ATLAS VIVO.
        
        Args:
            title: Work title
            doi: DOI of the work
            url: URL to the work
            work_type: Type of work (dataset, software, etc.)
            publication_date: Publication date (YYYY-MM-DD)
            
        Returns:
            Work payload
        """
        return {
            "title": {
                "title": {"value": title}
            },
            "type": work_type,
            "url": {"value": url},
            "external-ids": {
                "external-id": [
                    {
                        "external-id-type": "doi",
                        "external-id-value": doi,
                        "external-id-url": {"value": f"https://doi.org/{doi}"},
                        "external-id-relationship": "self"
                    }
                ]
            },
            "publication-date": {
                "year": {"value": publication_date[:4] if publication_date else str(datetime.now().year)},
                "month": {"value": publication_date[5:7] if publication_date else str(datetime.now().month)},
                "day": {"value": publication_date[8:10] if publication_date else str(datetime.now().day)}
            }
        }
    
    def link_work_to_orcid(self, orcid: str, work_data: Dict) -> Dict:
        """
        Link a work to researcher's ORCID record.
        
        Args:
            orcid: ORCID ID
            work_data: Work data
            
        Returns:
            Linking result
        """
        return self.add_work(orcid, work_data)
    
    def link_multiple_orcids(self, work_data: Dict, orcids: List[str]) -> Dict:
        """
        Link a work to multiple ORCID records.
        
        Args:
            work_data: Work data
            orcids: List of ORCID IDs
            
        Returns:
            Linking results for all ORCIDs
        """
        results = {}
        for orcid in orcids:
            try:
                result = self.link_work_to_orcid(orcid, work_data)
                results[orcid] = {"status": "success", "result": result}
            except Exception as e:
                results[orcid] = {"status": "error", "error": str(e)}
        
        return results
    
    def get_orcid_from_name(self, name: str) -> Optional[str]:
        """
        Search for ORCID by researcher name.
        
        Args:
            name: Researcher name
            
        Returns:
            ORCID ID if found, None otherwise
        """
        results = self.search_researchers(name)
        if results.get("result") and len(results["result"]) > 0:
            return results["result"][0].get("orcid-identifier", {}).get("path")
        return None
    
    def validate_orcid(self, orcid: str) -> bool:
        """
        Validate ORCID format.
        
        Args:
            orcid: ORCID to validate
            
        Returns:
            True if valid, False otherwise
        """
        import re
        pattern = r'^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$'
        return bool(re.match(pattern, orcid))


# Convenience function
orcid_api = None

def get_orcid_api(client_id: Optional[str] = None, 
                  client_secret: Optional[str] = None,
                  token: Optional[str] = None,
                  sandbox: bool = False) -> ORCIDAPI:
    """
    Get ORCID API client instance.
    
    Args:
        client_id: ORCID Client ID
        client_secret: ORCID Client Secret
        token: ORCID Access Token
        sandbox: Use sandbox environment
        
    Returns:
        ORCIDAPI instance
    """
    global orcid_api
    if orcid_api is None:
        orcid_api = ORCIDAPI(client_id, client_secret, token, sandbox)
    return orcid_api


if __name__ == "__main__":
    # Example usage
    print("ORCID API Client for ATLAS VIVO")
    print("=" * 50)
    
    try:
        # Initialize with environment variables
        api = get_orcid_api()
        print("✅ ORCID API client initialized successfully")
        
        # Test with known ORCID
        test_orcid = "0009-0009-1781-4020"  # Nuno's ORCID
        if api.validate_orcid(test_orcid):
            researcher = api.get_researcher(test_orcid)
            print(f"✅ API connection successful")
            print(f"   Retrieved info for ORCID: {test_orcid}")
        else:
            print(f"⚠️  ORCID {test_orcid} format validation failed")
        
    except Exception as e:
        print(f"❌ Error: {e}")
