"""
API clients for government data sources.

This module provides client classes for interacting with various government APIs
with built-in rate limiting, retries, and monitoring.
"""

import os
import time
import json
import logging
from typing import Dict, Any, Optional, List, Union, Tuple
import requests
from requests.adapters import HTTPAdapter, Retry
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse

from ...config import config
from ...db import get_db, APICallLog, APIKey
from ...db.models import MODELS

# Set up logging
logger = logging.getLogger(__name__)

class BaseAPIClient:
    """Base class for API clients with rate limiting and request tracking."""
    
    def __init__(
        self, 
        base_url: str, 
        service_name: str, 
        api_key: Optional[str] = None,
        rate_limit: int = 1000,
        retries: int = 3,
        backoff_factor: float = 0.5
    ):
        """
        Initialize the API client.
        
        Args:
            base_url: Base URL for the API
            service_name: Name of the service (for logging and monitoring)
            api_key: API key for authentication
            rate_limit: Maximum requests per minute
            retries: Number of retries for failed requests
            backoff_factor: Backoff factor for retries
        """
        self.base_url = base_url.rstrip('/')
        self.service_name = service_name
        self.api_key = api_key
        self.rate_limit = rate_limit
        self.requests_made = 0
        self.last_request_time = 0
        
        # Set up session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        self.session.headers.update({
            'User-Agent': f'{config.APP_NAME}/{config.ENV} (Python)',
            'Accept': 'application/json',
        })
        
        if self.api_key:
            self.session.headers['X-Api-Key'] = self.api_key
    
    def _enforce_rate_limit(self):
        """Enforce rate limiting by sleeping if necessary."""
        now = time.time()
        time_since_last_request = now - self.last_request_time
        
        # Calculate minimum time between requests to stay under rate limit
        min_interval = 60.0 / self.rate_limit
        
        if time_since_last_request < min_interval:
            sleep_time = min_interval - time_since_last_request
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _log_api_call(
        self, 
        method: str,
        endpoint: str,
        status_code: Optional[int] = None,
        response_time_ms: Optional[int] = None,
        success: Optional[bool] = None,
        error_message: Optional[str] = None,
        request_headers: Optional[Dict] = None,
        response_headers: Optional[Dict] = None,
        request_body: Optional[Union[Dict, str]] = None,
        response_body: Optional[Union[Dict, str]] = None
    ) -> str:
        """
        Log an API call to the database.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            status_code: HTTP status code
            response_time_ms: Response time in milliseconds
            success: Whether the request was successful
            error_message: Error message if the request failed
            request_headers: Request headers
            response_headers: Response headers
            request_body: Request body
            response_body: Response body
            
        Returns:
            The ID of the logged API call
        """
        db = next(get_db())
        
        # Convert request/response bodies to strings if they're dicts
        if isinstance(request_body, dict):
            request_body = json.dumps(request_body, ensure_ascii=False)
        if isinstance(response_body, dict):
            response_body = json.dumps(response_body, ensure_ascii=False)
        
        # Get API key ID if available
        api_key_id = None
        if self.api_key:
            api_key = db.query(APIKey).filter(APIKey.api_key == self.api_key).first()
            if api_key:
                api_key_id = str(api_key.id)
        
        # Create the log entry
        log_entry = APICallLog(
            api_key_id=api_key_id,
            service_name=self.service_name,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            success=success,
            error_message=error_message,
            request_headers=json.dumps(dict(request_headers)) if request_headers else None,
            response_headers=json.dumps(dict(response_headers)) if response_headers else None,
            request_body=request_body[:4000] if request_body else None,  # Truncate long bodies
            response_body=response_body[:4000] if response_body else None,
            ip_address=None,  # TODO: Get client IP if available
            user_agent=self.session.headers.get('User-Agent')
        )
        
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        
        return str(log_entry.id) if log_entry.id else None
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict] = None, 
        json_data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: int = 30,
        stream: bool = False,
        **kwargs
    ) -> Tuple[Optional[Union[Dict, str]], int, Dict]:
        """
        Make an HTTP request with rate limiting and error handling.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            params: Query parameters
            json_data: JSON request body
            headers: Additional headers
            timeout: Request timeout in seconds
            stream: Whether to stream the response
            **kwargs: Additional arguments to pass to requests.request()
            
        Returns:
            A tuple of (response_data, status_code, response_headers)
        """
        # Enforce rate limiting
        self._enforce_rate_limit()
        
        # Prepare request
        url = urljoin(self.base_url, endpoint.lstrip('/'))
        request_headers = self.session.headers.copy()
        if headers:
            request_headers.update(headers)
        
        # Log the request
        log_id = self._log_api_call(
            method=method,
            endpoint=endpoint,
            request_headers=request_headers,
            request_body=json_data if json_data else None,
            params=params
        )
        
        try:
            # Make the request
            start_time = time.time()
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=request_headers,
                timeout=timeout,
                stream=stream,
                **kwargs
            )
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Parse response
            try:
                response_data = response.json() if response.content else None
            except ValueError:
                response_data = response.text if response.content else None
            
            # Check for errors
            if not response.ok:
                error_message = f"{response.status_code} {response.reason}"
                if isinstance(response_data, dict):
                    error_message = response_data.get('message', error_message)
                elif response_data:
                    error_message = str(response_data)[:500]  # Truncate long error messages
                
                self._log_api_call(
                    method=method,
                    endpoint=endpoint,
                    status_code=response.status_code,
                    response_time_ms=response_time_ms,
                    success=False,
                    error_message=error_message,
                    request_headers=request_headers,
                    response_headers=dict(response.headers),
                    request_body=json_data if json_data else None,
                    response_body=response_data
                )
                
                response.raise_for_status()
            
            # Log successful request
            self._log_api_call(
                method=method,
                endpoint=endpoint,
                status_code=response.status_code,
                response_time_ms=response_time_ms,
                success=True,
                request_headers=request_headers,
                response_headers=dict(response.headers),
                request_body=json_data if json_data else None,
                response_body=response_data
            )
            
            return response_data, response.status_code, dict(response.headers)
            
        except Exception as e:
            error_time_ms = int((time.time() - start_time) * 1000) if 'start_time' in locals() else None
            
            # Log the error
            self._log_api_call(
                method=method,
                endpoint=endpoint,
                status_code=getattr(e.response, 'status_code', None) if 'e' in locals() and hasattr(e, 'response') else None,
                response_time_ms=error_time_ms,
                success=False,
                error_message=str(e),
                request_headers=request_headers,
                response_headers=dict(e.response.headers) if 'e' in locals() and hasattr(e, 'response') and hasattr(e.response, 'headers') else None,
                request_body=json_data if json_data else None,
                response_body=getattr(e, 'response', {}).text if 'e' in locals() and hasattr(e, 'response') else None
            )
            
            raise
    
    def get(self, endpoint: str, params: Optional[Dict] = None, **kwargs) -> Tuple[Optional[Union[Dict, str]], int, Dict]:
        """Make a GET request."""
        return self._make_request('GET', endpoint, params=params, **kwargs)
    
    def post(self, endpoint: str, json_data: Optional[Dict] = None, **kwargs) -> Tuple[Optional[Union[Dict, str]], int, Dict]:
        """Make a POST request."""
        return self._make_request('POST', endpoint, json_data=json_data, **kwargs)
    
    def put(self, endpoint: str, json_data: Optional[Dict] = None, **kwargs) -> Tuple[Optional[Union[Dict, str]], int, Dict]:
        """Make a PUT request."""
        return self._make_request('PUT', endpoint, json_data=json_data, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> Tuple[Optional[Union[Dict, str]], int, Dict]:
        """Make a DELETE request."""
        return self._make_request('DELETE', endpoint, **kwargs)


class CongressGovClient(BaseAPIClient):
    """Client for the Congress.gov API."""
    
    def __init__(self, api_key: Optional[str] = None, rate_limit: int = 1000):
        """Initialize the Congress.gov API client."""
        super().__init__(
            base_url=config.CONGRESS_GOV_API_BASE,
            service_name='congress_gov',
            api_key=api_key or config.CONGRESS_GOV_API_KEY,
            rate_limit=rate_limit or config.CONGRESS_GOV_RATE_LIMIT
        )
    
    def get_bill(self, congress: int, bill_type: str, bill_number: int) -> Dict:
        """Get details for a specific bill."""
        endpoint = f"bill/{congress}/{bill_type}/{bill_number}"
        response, status_code, _ = self.get(endpoint)
        return response
    
    def get_bill_actions(self, congress: int, bill_type: str, bill_number: int) -> Dict:
        """Get actions for a specific bill."""
        endpoint = f"bill/{congress}/{bill_type}/{bill_number}/actions"
        response, status_code, _ = self.get(endpoint)
        return response
    
    def get_bill_text(self, congress: int, bill_type: str, bill_number: int, format_type: str = 'text') -> Dict:
        """Get the text of a bill in the specified format."""
        endpoint = f"bill/{congress}/{bill_type}/{bill_number}/text/{format_type}"
        response, status_code, _ = self.get(endpoint)
        return response
    
    def get_bill_amendments(self, congress: int, bill_type: str, bill_number: int) -> Dict:
        """Get amendments for a specific bill."""
        endpoint = f"bill/{congress}/{bill_type}/{bill_number}/amendments"
        response, status_code, _ = self.get(endpoint)
        return response
    
    def get_bill_subjects(self, congress: int, bill_type: str, bill_number: int) -> Dict:
        """Get subjects for a specific bill."""
        endpoint = f"bill/{congress}/{bill_type}/{bill_number}/subjects"
        response, status_code, _ = self.get(endpoint)
        return response
    
    def get_bill_committees(self, congress: int, bill_type: str, bill_number: int) -> Dict:
        """Get committees for a specific bill."""
        endpoint = f"bill/{congress}/{bill_type}/{bill_number}/committees"
        response, status_code, _ = self.get(endpoint)
        return response
    
    def get_bill_cosponsors(self, congress: int, bill_type: str, bill_number: int) -> Dict:
        """Get cosponsors for a specific bill."""
        endpoint = f"bill/{congress}/{bill_type}/{bill_number}/cosponsors"
        response, status_code, _ = self.get(endpoint)
        return response
    
    def get_bill_relatedbills(self, congress: int, bill_type: str, bill_number: int) -> Dict:
        """Get related bills for a specific bill."""
        endpoint = f"bill/{congress}/{bill_type}/{bill_number}/relatedbills"
        response, status_code, _ = self.get(endpoint)
        return response
    
    def get_bill_subjects_bulk(self, congress: int, bill_type: Optional[str] = None) -> Dict:
        """Get subjects for all bills of a specific type in a Congress."""
        endpoint = f"bill/{congress}"
        if bill_type:
            endpoint += f"/{bill_type}"
        endpoint += "/subjects"
        response, status_code, _ = self.get(endpoint)
        return response
    
    def get_member(self, member_id: str) -> Dict:
        """Get details for a specific member of Congress."""
        endpoint = f"member/{member_id}"
        response, status_code, _ = self.get(endpoint)
        return response
    
    def get_member_bills(self, member_id: str, congress: Optional[int] = None, bill_type: Optional[str] = None) -> Dict:
        """Get bills sponsored or cosponsored by a member."""
        endpoint = f"member/{member_id}/bills"
        if congress:
            endpoint += f"/{congress}"
            if bill_type:
                endpoint += f"/{bill_type}"
        response, status_code, _ = self.get(endpoint)
        return response
    
    def search_bills(self, query: str, **params) -> Dict:
        """Search for bills."""
        endpoint = "bill"
        params['query'] = query
        response, status_code, _ = self.get(endpoint, params=params)
        return response


class GovInfoClient(BaseAPIClient):
    """Client for the GovInfo API."""
    
    def __init__(self, api_key: Optional[str] = None, rate_limit: int = 1000):
        """Initialize the GovInfo API client."""
        super().__init__(
            base_url=config.GOVINFO_API_BASE,
            service_name='govinfo',
            api_key=api_key or config.GOVINFO_API_KEY,
            rate_limit=rate_limit or config.GOVINFO_RATE_LIMIT
        )
    
    def get_collections(self) -> Dict:
        """Get a list of available collections."""
        endpoint = "/collections"
        response, status_code, _ = self.get(endpoint)
        return response
    
    def get_collection(self, collection_code: str) -> Dict:
        """Get details for a specific collection."""
        endpoint = f"/collections/{collection_code}"
        response, status_code, _ = self.get(endpoint)
        return response
    
    def get_collection_packages(
        self, 
        collection_code: str, 
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        offset: int = 0,
        page_size: int = 100,
        **params
    ) -> Dict:
        """Get packages in a collection."""
        endpoint = f"/collections/{collection_code}"
        
        # Add date range if provided
        if from_date or to_date:
            date_range = []
            if from_date:
                date_range.append(f"{from_date}T00:00:00Z")
            else:
                date_range.append("")
            
            if to_date:
                date_range.append(f"{to_date}T23:59:59Z")
            
            params['lastModified'] = '~'.join(date_range)
        
        # Add pagination
        params['offset'] = offset
        params['pageSize'] = page_size
        
        response, status_code, _ = self.get(endpoint, params=params)
        return response
    
    def get_package(self, package_id: str, **params) -> Dict:
        """Get details for a specific package."""
        endpoint = f"/packages/{package_id}"
        response, status_code, _ = self.get(endpoint, params=params)
        return response
    
    def get_package_summary(self, package_id: str) -> Dict:
        """Get summary for a specific package."""
        endpoint = f"/packages/{package_id}/summary"
        response, status_code, _ = self.get(endpoint)
        return response
    
    def get_package_content(self, package_id: str, file_name: str = 'mods.xml') -> str:
        """Get content for a specific package file."""
        endpoint = f"/packages/{package_id}/{file_name}"
        response, status_code, _ = self.get(endpoint)
        return response
    
    def download_package(self, package_id: str, output_dir: str) -> str:
        """Download a package and save it to disk."""
        # Get package details
        package = self.get_package(package_id)
        
        if not package or 'download' not in package or 'txtLink' not in package['download']:
            raise ValueError(f"No download URL found for package {package_id}")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Download the package
        download_url = package['download']['txtLink']
        file_name = os.path.basename(urlparse(download_url).path)
        output_path = os.path.join(output_dir, file_name)
        
        # Make the request with streaming to handle large files
        response = self.session.get(download_url, stream=True)
        response.raise_for_status()
        
        # Save the file
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        return output_path


class FederalRegisterClient(BaseAPIClient):
    """Client for the Federal Register API."""
    
    def __init__(self, api_key: Optional[str] = None, rate_limit: int = 1000):
        """Initialize the Federal Register API client."""
        super().__init__(
            base_url=config.FEDREG_API_BASE,
            service_name='federal_register',
            api_key=api_key or config.FEDREG_API_KEY,
            rate_limit=rate_limit or config.FEDREG_RATE_LIMIT
        )
    
    def get_document(self, document_number: str) -> Dict:
        """Get a specific Federal Register document."""
        endpoint = f"/documents/{document_number}.json"
        response, status_code, _ = self.get(endpoint)
        return response
    
    def search_documents(self, query: str, **params) -> Dict:
        """Search for Federal Register documents."""
        endpoint = "/documents.json"
        params['conditions[term]'] = query
        response, status_code, _ = self.get(endpoint, params=params)
        return response
    
    def get_public_inspection_documents(self, **params) -> Dict:
        """Get public inspection documents."""
        endpoint = "/public-inspection-documents/current.json"
        response, status_code, _ = self.get(endpoint, params=params)
        return response


class USASpendingClient(BaseAPIClient):
    """Client for the USAspending API."""
    
    def __init__(self, api_key: Optional[str] = None, rate_limit: int = 1000):
        """Initialize the USAspending API client."""
        super().__init__(
            base_url=config.USA_SPENDING_API_BASE,
            service_name='usaspending',
            api_key=api_key or config.USA_SPENDING_API_KEY,
            rate_limit=rate_limit or config.USA_SPENDING_RATE_LIMIT
        )
    
    def get_awards(self, **params) -> Dict:
        """Get award data."""
        endpoint = "/api/v2/awards/"
        response, status_code, _ = self.get(endpoint, params=params)
        return response
    
    def get_recipients(self, **params) -> Dict:
        """Get recipient data."""
        endpoint = "/api/v2/recipients/"
        response, status_code, _ = self.get(endpoint, params=params)
        return response
    
    def get_agencies(self, **params) -> Dict:
        """Get agency data."""
        endpoint = "/api/v2/references/agency/"
        response, status_code, _ = self.get(endpoint, params=params)
        return response
    
    def get_budget_functions(self, **params) -> Dict:
        """Get budget function data."""
        endpoint = "/api/v2/references/budget_functions/"
        response, status_code, _ = self.get(endpoint, params=params)
        return response


# Import the new client with Pydantic model support
from .congress_gov import CongressGovClient as PydanticCongressGovClient

# Create default client instances
congress_gov_client = CongressGovClient()
congress_gov_v2 = PydanticCongressGovClient()  # New version with Pydantic models
govinfo_client = GovInfoClient()
federal_register_client = FederalRegisterClient()
usaspending_client = USASpendingClient()

# Export the new client
__all__ = [
    'BaseAPIClient',
    'CongressGovClient',
    'PydanticCongressGovClient',  # Export the new client
    'GovInfoClient',
    'FederalRegisterClient',
    'USASpendingClient',
    'congress_gov_client',
    'congress_gov_v2',  # Export the new client instance
    'govinfo_client',
    'federal_register_client',
    'usaspending_client',
]
