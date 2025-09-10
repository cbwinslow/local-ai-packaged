"""
Test utilities for LocalAI and Ollama diagnostics.

This module provides utilities for testing and diagnosing issues with LocalAI and Ollama services.
"""

import json
import time
from typing import Dict, List, Optional, Union
import requests
from dataclasses import dataclass
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_diagnostics.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ServiceHealth:
    """Health status of a service."""
    service_name: str
    status: str
    response_time: float  # in seconds
    details: Optional[Dict] = None
    error: Optional[str] = None

class AIDiagnostics:
    """Base class for AI service diagnostics."""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        """Initialize with service base URL and optional API key."""
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}'
            })
    
    def check_health(self) -> ServiceHealth:
        """Check the health of the service."""
        raise NotImplementedError
    
    def test_completion(self, model: str, prompt: str) -> Dict:
        """Test text completion."""
        raise NotImplementedError
    
    def test_embedding(self, model: str, text: str) -> Dict:
        """Test text embedding."""
        raise NotImplementedError
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        retries: int = 3,
        backoff_factor: float = 0.5
    ) -> Dict:
        """Make an HTTP request with retry logic."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        for attempt in range(retries):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    timeout=30
                )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                if attempt == retries - 1:
                    logger.error(f"Request failed after {retries} attempts: {e}")
                    raise
                
                wait_time = backoff_factor * (2 ** attempt)
                logger.warning(f"Request failed (attempt {attempt + 1}/{retries}), retrying in {wait_time:.1f}s: {e}")
                time.sleep(wait_time)
        
        raise RuntimeError("All retry attempts failed")

class LocalAIDiagnostics(AIDiagnostics):
    """Diagnostics for LocalAI service."""
    
    def check_health(self) -> ServiceHealth:
        """Check LocalAI health status."""
        start_time = time.time()
        try:
            response = self._make_request('GET', '/health')
            return ServiceHealth(
                service_name='LocalAI',
                status='healthy',
                response_time=time.time() - start_time,
                details=response
            )
        except Exception as e:
            return ServiceHealth(
                service_name='LocalAI',
                status='unhealthy',
                response_time=time.time() - start_time,
                error=str(e)
            )
    
    def test_completion(self, model: str, prompt: str, **kwargs) -> Dict:
        """Test text completion with LocalAI."""
        data = {
            "model": model,
            "prompt": prompt,
            **kwargs
        }
        return self._make_request('POST', '/v1/completions', data=data)
    
    def test_embedding(self, model: str, text: str) -> Dict:
        """Test text embedding with LocalAI."""
        data = {
            "model": model,
            "input": text
        }
        return self._make_request('POST', '/v1/embeddings', data=data)

class OllamaDiagnostics(AIDiagnostics):
    """Diagnostics for Ollama service."""
    
    def check_health(self) -> ServiceHealth:
        """Check Ollama health status."""
        start_time = time.time()
        try:
            response = self._make_request('GET', '/api/tags')
            return ServiceHealth(
                service_name='Ollama',
                status='healthy',
                response_time=time.time() - start_time,
                details=response
            )
        except Exception as e:
            return ServiceHealth(
                service_name='Ollama',
                status='unhealthy',
                response_time=time.time() - start_time,
                error=str(e)
            )
    
    def test_completion(self, model: str, prompt: str, **kwargs) -> Dict:
        """Test text completion with Ollama."""
        data = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            **kwargs
        }
        return self._make_request('POST', '/api/generate', data=data)
    
    def test_embedding(self, model: str, text: str) -> Dict:
        """Test text embedding with Ollama."""
        data = {
            "model": model,
            "prompt": text
        }
        return self._make_request('POST', '/api/embeddings', data=data)

def run_diagnostics(service_url: str, service_type: str = 'localai', **kwargs) -> Dict:
    """Run diagnostics on the specified AI service.
    
    Args:
        service_url: Base URL of the service
        service_type: Type of service ('localai' or 'ollama')
        **kwargs: Additional arguments for the service
        
    Returns:
        Dictionary with diagnostic results
    """
    if service_type.lower() == 'localai':
        service = LocalAIDiagnostics(service_url, **kwargs)
    elif service_type.lower() == 'ollama':
        service = OllamaDiagnostics(service_url, **kwargs)
    else:
        raise ValueError(f"Unsupported service type: {service_type}")
    
    results = {}
    
    # Check service health
    health = service.check_health()
    results['health'] = health.__dict__
    
    if health.status != 'healthy':
        logger.error(f"Service is unhealthy: {health.error}")
        return results
    
    # Test with a simple prompt
    try:
        completion = service.test_completion(
            model=kwargs.get('model', 'gpt-4' if service_type == 'localai' else 'llama2'),
            prompt="What is the capital of France?",
            max_tokens=50
        )
        results['completion_test'] = completion
    except Exception as e:
        logger.error(f"Completion test failed: {e}")
        results['completion_test_error'] = str(e)
    
    # Test embeddings
    try:
        embedding = service.test_embedding(
            model=kwargs.get('embedding_model', 'text-embedding-ada-002' if service_type == 'localai' else 'llama2'),
            text="This is a test sentence."
        )
        results['embedding_test'] = {
            'status': 'success',
            'embedding_length': len(embedding.get('data', [{}])[0].get('embedding', [])) if service_type == 'localai' else len(embedding.get('embedding', []))
        }
    except Exception as e:
        logger.error(f"Embedding test failed: {e}")
        results['embedding_test_error'] = str(e)
    
    return results

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run AI service diagnostics')
    parser.add_argument('--url', required=True, help='Base URL of the AI service')
    parser.add_argument('--type', choices=['localai', 'ollama'], default='localai',
                       help='Type of AI service (default: localai)')
    parser.add_argument('--api-key', help='API key (if required)')
    parser.add_argument('--model', help='Model to test with')
    parser.add_argument('--embedding-model', help='Embedding model to test with')
    
    args = parser.parse_args()
    
    results = run_diagnostics(
        service_url=args.url,
        service_type=args.type,
        api_key=args.api_key,
        model=args.model,
        embedding_model=args.embedding_model
    )
    
    print("\nDiagnostic Results:")
    print(json.dumps(results, indent=2))
