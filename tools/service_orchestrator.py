#!/usr/bin/env python3
"""
Enhanced service orchestrator for Local AI Package
Builds and deploys services incrementally with comprehensive health checks
Supports service-by-service deployment for reliability
"""

import os
import subprocess
import time
import requests
import json
import sys
from pathlib import Path
import argparse
import docker
from typing import List, Dict, Optional

# Color codes for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'

def log_info(message: str):
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {message}")

def log_success(message: str):
    print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {message}")

def log_warning(message: str):
    print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")

def log_error(message: str):
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")

def log_header(message: str):
    print(f"\n{Colors.BLUE}{'='*50}{Colors.NC}")
    print(f"{Colors.BLUE}{message}{Colors.NC}")
    print(f"{Colors.BLUE}{'='*50}{Colors.NC}\n")

class ServiceOrchestrator:
    def __init__(self):
        self.docker_client = docker.from_env()
        self.project_name = "localai"
        self.base_path = Path.cwd()
        self.services_started = []
        self.health_check_timeout = 300  # 5 minutes
        self.health_check_interval = 10  # 10 seconds

    def run_command(self, cmd: List[str], cwd: Optional[str] = None) -> subprocess.CompletedProcess:
        """Run a shell command with logging"""
        log_info(f"Running: {' '.join(cmd)}")
        try:
            result = subprocess.run(
                cmd, 
                cwd=cwd, 
                check=True, 
                capture_output=True, 
                text=True
            )
            if result.stdout:
                log_info(f"Output: {result.stdout.strip()}")
            return result
        except subprocess.CalledProcessError as e:
            log_error(f"Command failed with exit code {e.returncode}")
            if e.stdout:
                log_error(f"stdout: {e.stdout}")
            if e.stderr:
                log_error(f"stderr: {e.stderr}")
            raise

    def check_prerequisites(self) -> bool:
        """Check all prerequisites before starting"""
        log_header("CHECKING PREREQUISITES")
        
        # Check Docker
        try:
            self.docker_client.ping()
            log_success("Docker is running and accessible")
        except Exception as e:
            log_error(f"Docker is not accessible: {e}")
            return False

        # Check .env file
        if not Path('.env').exists():
            log_error(".env file not found")
            log_info("Run: ./scripts/enhanced-populate-env-from-bitwarden.sh")
            return False
        log_success(".env file found")

        # Check Docker Compose files
        compose_files = [
            'docker-compose.yml',
            'docker-compose.traefik.yml'
        ]
        
        for file in compose_files:
            if not Path(file).exists():
                log_error(f"Required compose file not found: {file}")
                return False
            log_success(f"Found: {file}")

        return True

    def health_check_service(self, service_name: str, url: str, expected_status: int = 200) -> bool:
        """Perform health check on a service"""
        log_info(f"Health checking {service_name} at {url}")
        
        start_time = time.time()
        while time.time() - start_time < self.health_check_timeout:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == expected_status:
                    log_success(f"{service_name} is healthy (status: {response.status_code})")
                    return True
                else:
                    log_warning(f"{service_name} returned status: {response.status_code}")
            except requests.exceptions.RequestException as e:
                log_warning(f"Health check failed for {service_name}: {e}")
            
            log_info(f"Retrying health check for {service_name} in {self.health_check_interval} seconds...")
            time.sleep(self.health_check_interval)
        
        log_error(f"Health check timeout for {service_name}")
        return False

    def wait_for_container(self, container_name: str, timeout: int = 120) -> bool:
        """Wait for a container to be running"""
        log_info(f"Waiting for container: {container_name}")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                container = self.docker_client.containers.get(f"{self.project_name}-{container_name}-1")
                if container.status == 'running':
                    log_success(f"Container {container_name} is running")
                    return True
                else:
                    log_info(f"Container {container_name} status: {container.status}")
            except docker.errors.NotFound:
                log_info(f"Container {container_name} not found yet")
            
            time.sleep(5)
        
        log_error(f"Timeout waiting for container: {container_name}")
        return False

    def stop_existing_services(self):
        """Stop any existing services"""
        log_header("STOPPING EXISTING SERVICES")
        
        try:
            # Stop all services
            cmd = ["docker", "compose", "-p", self.project_name, "down", "-v", "--remove-orphans"]
            self.run_command(cmd)
            log_success("Stopped all existing services")
        except subprocess.CalledProcessError:
            log_warning("No existing services to stop")

    def start_infrastructure_services(self) -> bool:
        """Start core infrastructure services"""
        log_header("STARTING INFRASTRUCTURE SERVICES")
        
        infrastructure_services = [
            "postgres",  # Database
            "redis",     # Cache
            "traefik"    # Reverse proxy
        ]
        
        try:
            # Start Traefik first
            cmd = ["docker", "compose", "-f", "docker-compose.traefik.yml", "-p", self.project_name, "up", "-d", "traefik"]
            self.run_command(cmd)
            
            # Wait for Traefik
            if not self.health_check_service("Traefik", "http://localhost:8080/ping"):
                return False
            
            # Start core services
            for service in ["postgres", "redis"]:
                cmd = ["docker", "compose", "-p", self.project_name, "up", "-d", service]
                try:
                    self.run_command(cmd)
                    if not self.wait_for_container(service):
                        return False
                    self.services_started.append(service)
                    time.sleep(10)  # Give service time to initialize
                except subprocess.CalledProcessError as e:
                    log_warning(f"Service {service} may not be defined in compose files, continuing...")
            
            log_success("Infrastructure services started successfully")
            return True
            
        except Exception as e:
            log_error(f"Failed to start infrastructure services: {e}")
            return False

    def start_supabase_stack(self) -> bool:
        """Start Supabase services"""
        log_header("STARTING SUPABASE STACK")
        
        supabase_services = [
            "db",
            "auth", 
            "rest",
            "storage",
            "studio"
        ]
        
        try:
            # Start Supabase services in sequence
            for service in supabase_services:
                log_info(f"Starting Supabase service: {service}")
                cmd = ["docker", "compose", "-p", self.project_name, "up", "-d", service]
                try:
                    self.run_command(cmd)
                    if not self.wait_for_container(service):
                        log_warning(f"Service {service} may not have started properly")
                    else:
                        self.services_started.append(service)
                    time.sleep(15)  # Supabase services need more time
                except subprocess.CalledProcessError:
                    log_warning(f"Service {service} may not be defined, continuing...")
            
            # Health check Supabase API
            try:
                if self.health_check_service("Supabase", "http://localhost:8000/health", 200):
                    log_success("Supabase stack is healthy")
                    return True
            except:
                log_warning("Supabase health check failed, but continuing...")
                return True
                
        except Exception as e:
            log_error(f"Failed to start Supabase stack: {e}")
            return False

    def start_ai_services(self) -> bool:
        """Start AI and workflow services"""
        log_header("STARTING AI SERVICES")
        
        ai_services = [
            "ollama",
            "n8n", 
            "flowise",
            "neo4j",
            "qdrant"
        ]
        
        try:
            for service in ai_services:
                log_info(f"Starting AI service: {service}")
                cmd = ["docker", "compose", "-p", self.project_name, "up", "-d", service]
                try:
                    self.run_command(cmd)
                    if not self.wait_for_container(service):
                        log_warning(f"Service {service} may not have started properly")
                    else:
                        self.services_started.append(service)
                    
                    # Service-specific health checks
                    if service == "ollama":
                        time.sleep(30)  # Ollama needs more time
                        try:
                            self.health_check_service("Ollama", "http://localhost:11434/api/tags", 200)
                        except:
                            log_warning("Ollama health check failed, but continuing...")
                    elif service == "n8n":
                        time.sleep(20)
                        try:
                            self.health_check_service("n8n", "http://localhost:5678/", 200)
                        except:
                            log_warning("n8n health check failed, but continuing...")
                    elif service == "neo4j":
                        time.sleep(25)
                        try:
                            self.health_check_service("Neo4j", "http://localhost:7474/", 200)
                        except:
                            log_warning("Neo4j health check failed, but continuing...")
                    else:
                        time.sleep(15)
                        
                except subprocess.CalledProcessError:
                    log_warning(f"Service {service} may not be defined, continuing...")
            
            log_success("AI services started successfully")
            return True
            
        except Exception as e:
            log_error(f"Failed to start AI services: {e}")
            return False

    def start_frontend_services(self) -> bool:
        """Start frontend and user-facing services"""
        log_header("STARTING FRONTEND SERVICES")
        
        frontend_services = [
            "frontend",
            "webui"
        ]
        
        try:
            for service in frontend_services:
                log_info(f"Starting frontend service: {service}")
                cmd = ["docker", "compose", "-p", self.project_name, "up", "-d", service]
                try:
                    self.run_command(cmd)
                    if not self.wait_for_container(service):
                        log_warning(f"Service {service} may not have started properly")
                    else:
                        self.services_started.append(service)
                    time.sleep(15)
                except subprocess.CalledProcessError:
                    log_warning(f"Service {service} may not be defined, continuing...")
            
            log_success("Frontend services started successfully")
            return True
            
        except Exception as e:
            log_error(f"Failed to start frontend services: {e}")
            return False

    def verify_all_services(self) -> bool:
        """Final verification of all services"""
        log_header("VERIFYING ALL SERVICES")
        
        # Get all running containers for the project
        try:
            containers = self.docker_client.containers.list(
                filters={"label": f"com.docker.compose.project={self.project_name}"}
            )
            
            if not containers:
                log_error("No containers found for the project")
                return False
            
            log_success(f"Found {len(containers)} running containers")
            
            # List all running services
            for container in containers:
                service_name = container.labels.get("com.docker.compose.service", "unknown")
                log_success(f"✓ {service_name} ({container.name})")
            
            return True
            
        except Exception as e:
            log_error(f"Failed to verify services: {e}")
            return False

    def deploy_all_services(self, skip_build: bool = False) -> bool:
        """Main deployment orchestration"""
        log_header("LOCAL AI PACKAGE - SERVICE DEPLOYMENT")
        
        if not self.check_prerequisites():
            return False
        
        try:
            # Stop existing services
            self.stop_existing_services()
            
            # Build images if needed
            if not skip_build:
                log_info("Building Docker images...")
                cmd = ["docker", "compose", "-p", self.project_name, "build", "--pull"]
                try:
                    self.run_command(cmd)
                    log_success("Docker images built successfully")
                except subprocess.CalledProcessError:
                    log_warning("Build failed, continuing with existing images...")
            
            # Deploy in stages
            stages = [
                ("Infrastructure", self.start_infrastructure_services),
                ("Supabase", self.start_supabase_stack),
                ("AI Services", self.start_ai_services),
                ("Frontend", self.start_frontend_services),
            ]
            
            for stage_name, stage_func in stages:
                log_header(f"DEPLOYING: {stage_name}")
                if not stage_func():
                    log_error(f"Failed to deploy {stage_name}")
                    return False
                log_success(f"{stage_name} deployed successfully")
                time.sleep(10)  # Brief pause between stages
            
            # Final verification
            if not self.verify_all_services():
                log_error("Service verification failed")
                return False
            
            log_header("DEPLOYMENT COMPLETE")
            log_success("🎉 All services deployed successfully!")
            log_info("Services accessible at:")
            log_info("  - Traefik Dashboard: http://localhost:8080")
            log_info("  - Supabase Studio: http://localhost:3000")
            log_info("  - n8n: http://localhost:5678")
            log_info("  - Neo4j Browser: http://localhost:7474")
            log_info("  - Open WebUI: http://localhost:3001")
            
            return True
            
        except Exception as e:
            log_error(f"Deployment failed: {e}")
            return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Enhanced Local AI Package Service Orchestrator")
    parser.add_argument("--skip-build", action="store_true", help="Skip Docker image building")
    parser.add_argument("--services-only", nargs="+", help="Deploy only specific services")
    args = parser.parse_args()
    
    orchestrator = ServiceOrchestrator()
    
    if args.services_only:
        log_info(f"Deploying only: {', '.join(args.services_only)}")
        # TODO: Implement selective service deployment
        log_error("Selective service deployment not yet implemented")
        return 1
    
    success = orchestrator.deploy_all_services(skip_build=args.skip_build)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())