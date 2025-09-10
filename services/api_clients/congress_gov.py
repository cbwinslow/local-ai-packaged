"""
Congress.gov API client with Pydantic model support.
"""

import logging
from typing import Dict, Any, Optional, List, Union, Tuple, Type, TypeVar
from datetime import datetime
import json

from sqlalchemy.orm import Session
from pydantic import BaseModel, validator, HttpUrl, parse_obj_as
import requests

from ...models import (
    Bill, BillAction, BillSubject, BillCosponsor, Member, 
    PaginatedResponse, APIResponse, APIParams
)
from ...db import get_db
from ...config import config
from .base import BaseAPIClient

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)

class CongressGovClient(BaseAPIClient):
    """Client for the Congress.gov API with Pydantic model support."""
    
    def __init__(self, api_key: Optional[str] = None, rate_limit: int = 1000):
        """Initialize the Congress.gov API client.
        
        Args:
            api_key: API key for authentication
            rate_limit: Maximum requests per minute
        """
        super().__init__(
            base_url=config.CONGRESS_GOV_API_BASE,
            service_name='congress_gov',
            api_key=api_key or config.CONGRESS_GOV_API_KEY,
            rate_limit=rate_limit or config.CONGRESS_GOV_RATE_LIMIT
        )
    
    def _parse_response(self, response: requests.Response, model: Type[T]) -> T:
        """Parse an API response into a Pydantic model.
        
        Args:
            response: HTTP response
            model: Pydantic model class
            
        Returns:
            Parsed model instance
            
        Raises:
            ValueError: If the response cannot be parsed
        """
        try:
            data = response.json()
            return model.parse_obj(data)
        except Exception as e:
            logger.error(f"Failed to parse response: {e}")
            raise ValueError(f"Failed to parse response: {e}")
    
    def _paginated_request(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        model: Optional[Type[T]] = None
    ) -> PaginatedResponse[T]:
        """Make a paginated API request.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            model: Pydantic model for items
            
        Returns:
            Paginated response with items of type T
        """
        if params is None:
            params = {}
        
        # Add API key if not present
        if 'api_key' not in params and self.api_key:
            params['api_key'] = self.api_key
        
        # Make request
        response = self._make_request('GET', endpoint, params=params)
        
        # Parse response
        data = response.json()
        
        # Extract pagination info
        pagination = data.get('pagination', {})
        
        # Parse items if model is provided
        items = data.get('items', [])
        if model:
            items = [model.parse_obj(item) for item in items]
        
        return PaginatedResponse[
            model or Dict[str, Any]  # type: ignore
        ](
            items=items,
            pagination=pagination,
            status=response.status_code,
            url=response.url,
            headers=dict(response.headers),
        )
    
    def get_bill(
        self, 
        congress: int, 
        bill_type: str, 
        bill_number: int,
        params: Optional[APIParams] = None
    ) -> APIResponse[Bill]:
        """Get details for a specific bill.
        
        Args:
            congress: Congress number (e.g., 117)
            bill_type: Bill type (e.g., 'hr', 's', 'hres')
            bill_number: Bill number
            params: Additional API parameters
            
        Returns:
            API response with bill data
        """
        endpoint = f"{congress}/bills/{bill_type}{bill_number}.json"
        
        # Convert Pydantic model to dict for request
        request_params = {}
        if params:
            request_params = params.dict(exclude_none=True)
        
        response = self._make_request('GET', endpoint, params=request_params)
        data = response.json()
        
        # Extract bill data from response
        bill_data = data.get('bill', {})
        
        return APIResponse[Bill](
            data=Bill.parse_obj(bill_data),
            status=response.status_code,
            url=response.url,
            headers=dict(response.headers),
        )
    
    def get_bill_actions(
        self, 
        congress: int, 
        bill_type: str, 
        bill_number: int,
        params: Optional[APIParams] = None
    ) -> APIResponse[List[BillAction]]:
        """Get actions for a specific bill.
        
        Args:
            congress: Congress number
            bill_type: Bill type (e.g., 'hr', 's')
            bill_number: Bill number
            params: Additional API parameters
            
        Returns:
            API response with list of bill actions
        """
        endpoint = f"{congress}/bills/{bill_type}{bill_number}/actions.json"
        
        # Convert Pydantic model to dict for request
        request_params = {}
        if params:
            request_params = params.dict(exclude_none=True)
        
        response = self._make_request('GET', endpoint, params=request_params)
        data = response.json()
        
        # Extract actions from response
        actions = data.get('actions', [])
        
        return APIResponse[List[BillAction]](
            data=[BillAction.parse_obj(action) for action in actions],
            status=response.status_code,
            url=response.url,
            headers=dict(response.headers),
        )
    
    def get_bill_subjects(
        self, 
        congress: int, 
        bill_type: str, 
        bill_number: int,
        params: Optional[APIParams] = None
    ) -> APIResponse[List[BillSubject]]:
        """Get subjects for a specific bill.
        
        Args:
            congress: Congress number
            bill_type: Bill type (e.g., 'hr', 's')
            bill_number: Bill number
            params: Additional API parameters
            
        Returns:
            API response with list of bill subjects
        """
        endpoint = f"{congress}/bills/{bill_type}{bill_number}/subjects.json"
        
        # Convert Pydantic model to dict for request
        request_params = {}
        if params:
            request_params = params.dict(exclude_none=True)
        
        response = self._make_request('GET', endpoint, params=request_params)
        data = response.json()
        
        # Extract subjects from response
        subjects = data.get('subjects', [])
        
        return APIResponse[List[BillSubject]](
            data=[BillSubject.parse_obj(subject) for subject in subjects],
            status=response.status_code,
            url=response.url,
            headers=dict(response.headers),
        )
    
    def get_bill_cosponsors(
        self, 
        congress: int, 
        bill_type: str, 
        bill_number: int,
        params: Optional[APIParams] = None
    ) -> APIResponse[List[BillCosponsor]]:
        """Get cosponsors for a specific bill.
        
        Args:
            congress: Congress number
            bill_type: Bill type (e.g., 'hr', 's')
            bill_number: Bill number
            params: Additional API parameters
            
        Returns:
            API response with list of bill cosponsors
        """
        endpoint = f"{congress}/bills/{bill_type}{bill_number}/cosponsors.json"
        
        # Convert Pydantic model to dict for request
        request_params = {}
        if params:
            request_params = params.dict(exclude_none=True)
        
        response = self._make_request('GET', endpoint, params=request_params)
        data = response.json()
        
        # Extract cosponsors from response
        cosponsors = data.get('cosponsors', [])
        
        return APIResponse[List[BillCosponsor]](
            data=[BillCosponsor.parse_obj(cosponsor) for cosponsor in cosponsors],
            status=response.status_code,
            url=response.url,
            headers=dict(response.headers),
        )
    
    def get_member(
        self, 
        member_id: str,
        params: Optional[APIParams] = None
    ) -> APIResponse[Member]:
        """Get details for a specific member of Congress.
        
        Args:
            member_id: Bioguide ID of the member
            params: Additional API parameters
            
        Returns:
            API response with member data
        """
        endpoint = f"member/{member_id}.json"
        
        # Convert Pydantic model to dict for request
        request_params = {}
        if params:
            request_params = params.dict(exclude_none=True)
        
        response = self._make_request('GET', endpoint, params=request_params)
        data = response.json()
        
        # Extract member data from response
        member_data = data.get('member', {})
        
        return APIResponse[Member](
            data=Member.parse_obj(member_data),
            status=response.status_code,
            url=response.url,
            headers=dict(response.headers),
        )
    
    def search_bills(
        self, 
        query: str,
        params: Optional[APIParams] = None
    ) -> PaginatedResponse[Bill]:
        """Search for bills.
        
        Args:
            query: Search query
            params: Additional API parameters
            
        Returns:
            Paginated response with matching bills
        """
        endpoint = "bills/search.json"
        
        # Add query to parameters
        if params is None:
            params = APIParams()
        
        # Convert Pydantic model to dict for request
        request_params = params.dict(exclude_none=True)
        request_params['query'] = query
        
        return self._paginated_request(endpoint, request_params, model=Bill)

# Create a default client instance
congress_gov_client = CongressGovClient()
