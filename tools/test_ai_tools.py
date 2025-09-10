#!/usr/bin/env python3
"""
AI Tools Integration Tests

This script tests the integration of various AI tools and services.
"""

import os
import sys
import time
import requests
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AIToolsTester:
    def __init__(self):
        self.results = {}
        self.services = {
            'graphite': {
                'url': f"http://localhost:{os.getenv('GRAPHITE_PORT', '8080')}",
                'endpoint': '/dashboard',
                'expected_status': 200
            },
            'libsql': {
                'url': f"http://localhost:{os.getenv('LIBSQL_PORT', '8081')}",
                'endpoint': '/',
                'expected_status': 200
            },
            'neo4j': {
                'url': f"http://localhost:{os.getenv('NEO4J_HTTP_PORT', '7474')}",
                'endpoint': '/browser/',
                'expected_status': 200
            },
            'crewai': {
                'url': f"http://localhost:{os.getenv('CREWAI_PORT', '8000')}",
                'endpoint': '/',
                'expected_status': 200
            },
            'letta': {
                'url': f"http://localhost:{os.getenv('LETTA_PORT', '8001')}",
                'endpoint': '/',
                'expected_status': 200
            },
            'falkor': {
                'url': f"http://localhost:{os.getenv('FALKOR_PORT', '6379')}",
                'endpoint': '',
                'skip': True  # Skip direct HTTP test for Redis
            },
            'graphrag': {
                'url': f"http://localhost:{os.getenv('GRAPHRAG_PORT', '8002')}",
                'endpoint': '/',
                'expected_status': 200
            },
            'llama': {
                'url': f"http://localhost:{os.getenv('LLAMA_PORT', '8003')}",
                'endpoint': '/',
                'expected_status': 200
            },
            'crawl4ai': {
                'url': f"http://localhost:{os.getenv('CRAWL4AI_PORT', '8004')}",
                'endpoint': '/',
                'expected_status': 200
            }
        }
    
    def test_service(self, service_name, config):
        """Test a single service."""
        if config.get('skip', False):
            print(f"Skipping {service_name} (marked to skip)")
            self.results[service_name] = {'status': 'skipped', 'message': 'Skipped by configuration'}
            return True
            
        url = f"{config['url']}{config['endpoint']}"
        print(f"Testing {service_name} at {url}...")
        
        try:
            response = requests.get(url, timeout=10)
            status_ok = response.status_code == config['expected_status']
            self.results[service_name] = {
                'status': 'success' if status_ok else 'failed',
                'status_code': response.status_code,
                'expected_status': config['expected_status']
            }
            return status_ok
        except requests.exceptions.RequestException as e:
            print(f"  Error: {str(e)}")
            self.results[service_name] = {
                'status': 'error',
                'error': str(e)
            }
            return False
    
    def test_all_services(self):
        """Test all configured services."""
        print("=== Starting AI Tools Integration Tests ===\n")
        
        all_success = True
        for service_name, config in self.services.items():
            if not self.test_service(service_name, config):
                all_success = False
            time.sleep(1)  # Be nice to the services
        
        # Print summary
        print("\n=== Test Results ===")
        for service, result in self.results.items():
            status = result['status']
            if status == 'success':
                print(f"✅ {service}: {status}")
            elif status == 'skipped':
                print(f"⏩ {service}: {status} - {result['message']}")
            else:
                print(f"❌ {service}: {status} - {result.get('error', 'Unknown error')}")
        
        return all_success

if __name__ == "__main__":
    tester = AIToolsTester()
    success = tester.test_all_services()
    
    # Save results to file
    with open('ai_tools_test_results.json', 'w') as f:
        json.dump(tester.results, f, indent=2)
    
    sys.exit(0 if success else 1)
