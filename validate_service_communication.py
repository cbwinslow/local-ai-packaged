#!/usr/bin/env python3
"""
Validation script to test Docker service communication and startup
This script validates the configuration without fully deploying all services
"""

import subprocess
import sys
import time
import requests
import os

def test_traefik_startup():
    """Test that Traefik can start and is accessible"""
    print("🧪 Testing Traefik startup...")
    
    try:
        # Start only Traefik
        subprocess.run([
            "docker", "compose", "-p", "localai-test", 
            "-f", "docker-compose.traefik.yml", 
            "up", "-d"
        ], check=True, capture_output=True)
        
        # Wait a bit for startup
        time.sleep(5)
        
        # Test that Traefik dashboard is accessible
        try:
            response = requests.get("http://localhost:8080/ping", timeout=5)
            if response.status_code == 200:
                print("✅ Traefik started successfully and is responding")
                return True
            else:
                print(f"⚠️  Traefik responded with status {response.status_code}")
                return False
        except requests.exceptions.RequestException:
            print("❌ Traefik is not responding on port 8080")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start Traefik: {e}")
        return False
    finally:
        # Clean up
        try:
            subprocess.run([
                "docker", "compose", "-p", "localai-test",
                "-f", "docker-compose.traefik.yml", 
                "down"
            ], capture_output=True)
        except:
            pass

def test_network_creation():
    """Test that Docker network can be created properly"""
    print("🧪 Testing Docker network creation...")
    
    try:
        # Try to create the network
        result = subprocess.run([
            "docker", "network", "create", "test-localai-network"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Docker network creation works")
            
            # Clean up
            subprocess.run([
                "docker", "network", "rm", "test-localai-network"
            ], capture_output=True)
            return True
        else:
            print(f"❌ Failed to create Docker network: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Network creation test failed: {e}")
        return False

def test_service_dependencies():
    """Test that service dependencies are properly configured"""
    print("🧪 Testing service dependencies...")
    
    try:
        # Parse docker-compose to check dependencies
        result = subprocess.run([
            "docker", "compose", "config"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            config = result.stdout
            
            # Check that services with dependencies are properly configured
            dependency_checks = [
                ("agentic-rag", ["neo4j", "postgres", "qdrant"]),
                ("langfuse-web", ["postgres", "minio", "redis", "clickhouse"]),
                ("n8n", ["postgres"])
            ]
            
            all_good = True
            for service, deps in dependency_checks:
                if service in config:
                    for dep in deps:
                        if f"depends_on" in config and dep in config:
                            continue
                        else:
                            print(f"⚠️  Service {service} may be missing dependency on {dep}")
                            all_good = False
            
            if all_good:
                print("✅ Service dependencies are properly configured")
            return all_good
        else:
            print(f"❌ Failed to parse docker-compose config: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Dependency test failed: {e}")
        return False

def test_environment_variables():
    """Test that required environment variables are set"""
    print("🧪 Testing environment variables...")
    
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        return False
    
    required_vars = [
        'POSTGRES_PASSWORD',
        'JWT_SECRET', 
        'NEO4J_AUTH',
        'LANGFUSE_SALT',
        'NEXTAUTH_SECRET',
        'ENCRYPTION_KEY'
    ]
    
    with open('.env', 'r') as f:
        env_content = f.read()
    
    missing_vars = []
    for var in required_vars:
        if f'{var}=' not in env_content or f'{var}=your-' in env_content or f'{var}=super-secret' in env_content:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing or default values for: {', '.join(missing_vars)}")
        return False
    else:
        print("✅ Required environment variables are set")
        return True

def main():
    """Run validation tests"""
    print("🔬 Running Docker Service Communication Validation")
    print("=" * 60)
    
    # Skip tests that require ports 80/443 in this environment
    if os.environ.get('CI') or os.environ.get('GITHUB_ACTIONS'):
        print("🚀 Running in CI environment - skipping port-dependent tests")
        tests = [
            test_network_creation,
            test_service_dependencies,
            test_environment_variables
        ]
    else:
        tests = [
            test_network_creation,
            test_service_dependencies, 
            test_environment_variables,
            test_traefik_startup
        ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
        print()
    
    if all(results):
        print("🎉 All validation tests passed! Services should communicate properly.")
        return 0
    else:
        print("❌ Some validation tests failed. Check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())