"""
Government API Documentation and Rate Limit Tracker.

This module documents various government API endpoints and their rate limits,
and provides utilities to track and respect those limits.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class APIType(str, Enum):
    """Types of government APIs."""
    LEGISLATIVE = "legislative"
    EXECUTIVE = "executive"
    JUDICIAL = "judicial"
    REGULATORY = "regulatory"
    OTHER = "other"

@dataclass
class RateLimit:
    """Represents rate limits for an API endpoint."""
    requests_per_second: Optional[int] = None
    requests_per_minute: Optional[int] = None
    requests_per_hour: Optional[int] = None
    requests_per_day: Optional[int] = None
    
    def get_min_interval(self) -> Optional[float]:
        """Get the minimum interval between requests in seconds."""
        if self.requests_per_second:
            return 1.0 / self.requests_per_second
        if self.requests_per_minute:
            return 60.0 / self.requests_per_minute
        if self.requests_per_hour:
            return 3600.0 / self.requests_per_hour
        if self.requests_per_day:
            return 86400.0 / self.requests_per_day
        return None

@dataclass
class APIEndpoint:
    """Represents a government API endpoint."""
    name: str
    base_url: str
    description: str
    api_type: APIType
    rate_limit: RateLimit
    documentation_url: str
    requires_auth: bool = False
    auth_type: Optional[str] = None
    notes: str = ""
    last_request_time: Optional[datetime] = None
    request_count: Dict[str, int] = field(default_factory=dict)

class GovAPITracker:
    """Tracks API usage and enforces rate limits."""
    
    def __init__(self):
        self.endpoints: Dict[str, APIEndpoint] = {}
        self._init_known_apis()
    
    def _init_known_apis(self):
        """Initialize with known government API endpoints."""
        # GovInfo Bulk Data API (no rate limit)
        self.add_endpoint(
            APIEndpoint(
                name="GovInfo Bulk Data",
                base_url="https://www.govinfo.gov/bulkdata",
                description="Bulk data downloads from US Government Publishing Office",
                api_type=APIType.LEGISLATIVE,
                rate_limit=RateLimit(),  # No rate limit
                documentation_url="https://www.govinfo.gov/bulk-downloads",
                notes="No rate limits, but be considerate of server load"
            )
        )
        
        # Congress API (ProPublica)
        self.add_endpoint(
            APIEndpoint(
                name="ProPublica Congress API",
                base_url="https://api.propublica.org/congress/v1",
                description="Access to Congressional data including bills, votes, and members",
                api_type=APIType.LEGISLATIVE,
                rate_limit=RateLimit(requests_per_second=5),  # 5 requests per second
                documentation_url="https://projects.propublica.org/api-docs/congress-api/",
                requires_auth=True,
                auth_type="API Key",
                notes="Requires API key from ProPublica"
            )
        )
        
        # Regulations.gov API
        self.add_endpoint(
            APIEndpoint(
                name="Regulations.gov API",
                base_url="https://api.regulations.gov/v4",
                description="Access to federal regulatory information",
                api_type=APIType.REGULATORY,
                rate_limit=RateLimit(requests_per_minute=1000),  # 1000 requests per minute
                documentation_url="https://open.gsa.gov/api/regulationsgov/",
                requires_auth=True,
                auth_type="API Key"
            )
        )
        
        # Federal Register API
        self.add_endpoint(
            APIEndpoint(
                name="Federal Register API",
                base_url="https://www.federalregister.gov/api/v1",
                description="Access to Federal Register documents and metadata",
                api_type=APIType.REGULATORY,
                rate_limit=RateLimit(requests_per_second=10),  # 10 requests per second
                documentation_url="https://www.federalregister.gov/developers/api/v2",
                requires_auth=True,
                auth_type="API Key"
            )
        )
        
        # USAspending API
        self.add_endpoint(
            APIEndpoint(
                name="USAspending API",
                base_url="https://api.usaspending.gov/api/v2",
                description="Access to US government spending data",
                api_type=APIType.EXECUTIVE,
                rate_limit=RateLimit(requests_per_minute=60),  # 60 requests per minute
                documentation_url="https://api.usaspending.gov/docs/",
                requires_auth=False
            )
        )
    
    def add_endpoint(self, endpoint: APIEndpoint):
        """Add or update an API endpoint."""
        self.endpoints[endpoint.name] = endpoint
        logger.info(f"Added/updated API endpoint: {endpoint.name}")
    
    def get_endpoint(self, name: str) -> Optional[APIEndpoint]:
        """Get an API endpoint by name."""
        return self.endpoints.get(name)
    
    def list_endpoints(self, api_type: Optional[APIType] = None) -> List[APIEndpoint]:
        """List all endpoints, optionally filtered by type."""
        if api_type:
            return [ep for ep in self.endpoints.values() if ep.api_type == api_type]
        return list(self.endpoints.values())
    
    def record_request(self, endpoint_name: str):
        """Record an API request and enforce rate limits."""
        endpoint = self.endpoints.get(endpoint_name)
        if not endpoint:
            logger.warning(f"Unknown endpoint: {endpoint_name}")
            return
        
        now = datetime.utcnow()
        
        # Update request count for the current minute
        minute_key = now.strftime("%Y-%m-%dT%H:%M")
        endpoint.request_count[minute_key] = endpoint.request_count.get(minute_key, 0) + 1
        
        # Check rate limits
        if endpoint.rate_limit.requests_per_second:
            if endpoint.last_request_time:
                min_interval = 1.0 / endpoint.rate_limit.requests_per_second
                elapsed = (now - endpoint.last_request_time).total_seconds()
                if elapsed < min_interval:
                    sleep_time = min_interval - elapsed
                    logger.debug(f"Rate limit: sleeping for {sleep_time:.2f} seconds")
                    time.sleep(sleep_time)
        
        if endpoint.rate_limit.requests_per_minute:
            current_minute = now.strftime("%Y-%m-%dT%H:%M")
            minute_count = sum(
                count for key, count in endpoint.request_count.items()
                if key == current_minute
            )
            if minute_count > endpoint.rate_limit.requests_per_minute:
                logger.warning("Approaching rate limit for this minute. Consider adding a delay.")
        
        # Clean up old request counts
        cutoff = now - timedelta(hours=1)
        endpoint.request_count = {
            k: v for k, v in endpoint.request_count.items()
            if datetime.strptime(k, "%Y-%m-%dT%H:%M") > cutoff
        }
        
        endpoint.last_request_time = now

# Example usage
if __name__ == "__main__":
    # Initialize the tracker
    tracker = GovAPITracker()
    
    # List all available endpoints
    print("Available Government API Endpoints:")
    print("=" * 50)
    for endpoint in tracker.list_endpoints():
        print(f"\n{endpoint.name}")
        print(f"  URL: {endpoint.base_url}")
        print(f"  Type: {endpoint.api_type.value}")
        print(f"  Requires Auth: {'Yes' if endpoint.requires_auth else 'No'}")
        if endpoint.requires_auth and endpoint.auth_type:
            print(f"  Auth Type: {endpoint.auth_type}")
        print(f"  Rate Limits:")
        if endpoint.rate_limit.requests_per_second:
            print(f"    - {endpoint.rate_limit.requests_per_second} requests/second")
        if endpoint.rate_limit.requests_per_minute:
            print(f"    - {endpoint.rate_limit.requests_per_minute} requests/minute")
        if endpoint.rate_limit.requests_per_hour:
            print(f"    - {endpoint.rate_limit.requests_per_hour} requests/hour")
        if endpoint.rate_limit.requests_per_day:
            print(f"    - {endpoint.rate_limit.requests_per_day} requests/day")
        if endpoint.notes:
            print(f"  Notes: {endpoint.notes}")
    
    print("\nExample of using the rate limiter:")
    endpoint_name = "ProPublica Congress API"
    endpoint = tracker.get_endpoint(endpoint_name)
    if endpoint:
        print(f"\nMaking requests to {endpoint_name} with rate limiting:")
        for i in range(3):
            tracker.record_request(endpoint_name)
            print(f"  Request {i+1} at {datetime.utcnow().isoformat()}")
    else:
        print(f"\nEndpoint not found: {endpoint_name}")
