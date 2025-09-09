#!/usr/bin/env python3
"""
# =============================================================================
# Name: start_services.py
# Date: 2024-12-28
# Script Name: start_services.py
# Version: 2.0.0
# Log Summary: Complete rewrite to implement single-entrypoint orchestration
# Description: Comprehensive orchestration script for local and remote deployment
#              of self-hosted AI and Supabase services with Docker. Provides CLI
#              subcommands for initialization, deployment, management, diagnostics,
#              and remote deployment capabilities.
# Change Summary: 
#   - Added rich CLI with subcommands (init, up, down, restart, logs, status, test, deploy-remote, destroy-remote)
#   - Implemented comprehensive logging and environment validation
#   - Added complete diagnostics and health check suite
#   - Implemented remote deployment via SSH with idempotent setup
#   - Added robust error handling and structured logging
#   - Enhanced Supabase integration and secrets management
# Inputs: Command line arguments and subcommands, .env file, docker-compose files
# Outputs: Service orchestration, logs, health status, deployment confirmation
# =============================================================================
"""

import os
import sys
import json
import time
import shutil
import logging
import argparse
import platform
import subprocess
import threading
import tempfile
import secrets
import string
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from contextlib import contextmanager

# Version information
__version__ = "2.0.0"
__author__ = "Local AI Package Team"

# Constants
PROJECT_NAME = "localai"
LOGS_DIR = "logs"
SUPABASE_REPO_URL = "https://github.com/supabase/supabase.git"
DEFAULT_TIMEOUT = 300
HEALTH_CHECK_TIMEOUT = 120
SSH_TIMEOUT = 30

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels."""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)

class ServiceOrchestrator:
    """Main orchestration class for local AI and Supabase services."""
    
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        self.project_root = Path.cwd()
        self.ensure_logs_directory()
        
    def setup_logging(self):
        """Set up structured logging with file and console handlers."""
        # Create logs directory if it doesn't exist
        logs_dir = Path(LOGS_DIR)
        logs_dir.mkdir(exist_ok=True)
        
        # Configure root logger
        logging.basicConfig(level=logging.INFO, handlers=[])
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        
        # File handler with detailed format
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = logs_dir / f"orchestrator_{timestamp}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        # Console handler with colored output
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = ColoredFormatter(
            '%(levelname)s: %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
    def ensure_logs_directory(self):
        """Ensure logs directory exists and is properly configured."""
        logs_dir = Path(LOGS_DIR)
        logs_dir.mkdir(exist_ok=True)
        
        # Create .gitkeep if directory is empty
        if not any(logs_dir.iterdir()):
            (logs_dir / ".gitkeep").touch()
            
    def run_command(self, cmd: List[str], cwd: Optional[str] = None, 
                   capture_output: bool = False, timeout: int = DEFAULT_TIMEOUT) -> subprocess.CompletedProcess:
        """Run a shell command with proper logging and error handling."""
        cmd_str = " ".join(cmd)
        self.logger.debug(f"Running command: {cmd_str}")
        
        try:
            if capture_output:
                result = subprocess.run(
                    cmd, cwd=cwd, capture_output=True, text=True, 
                    timeout=timeout, check=True
                )
            else:
                self.logger.info(f"Executing: {cmd_str}")
                result = subprocess.run(cmd, cwd=cwd, timeout=timeout, check=True)
            return result
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command failed: {cmd_str}")
            if hasattr(e, 'stderr') and e.stderr:
                self.logger.error(f"Error output: {e.stderr}")
            raise
        except subprocess.TimeoutExpired:
            self.logger.error(f"Command timed out after {timeout}s: {cmd_str}")
            raise
            
    def generate_secret(self, length: int = 32) -> str:
        """Generate a cryptographically secure random secret."""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
        
    def generate_hex_secret(self, length: int = 32) -> str:
        """Generate a hex secret using openssl or fallback method."""
        try:
            result = self.run_command(["openssl", "rand", "-hex", str(length)], capture_output=True)
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.logger.warning("OpenSSL not available, using fallback secret generation")
            return secrets.token_hex(length)
            
    def validate_docker_installation(self) -> bool:
        """Validate Docker and Docker Compose are installed and running."""
        self.logger.info("Validating Docker installation...")
        
        try:
            # Check Docker
            result = self.run_command(["docker", "--version"], capture_output=True)
            self.logger.info(f"Docker version: {result.stdout.strip()}")
            
            # Check Docker Compose
            result = self.run_command(["docker", "compose", "version"], capture_output=True)
            self.logger.info(f"Docker Compose version: {result.stdout.strip()}")
            
            # Check if Docker daemon is running
            self.run_command(["docker", "info"], capture_output=True)
            self.logger.info("Docker daemon is running")
            
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            self.logger.error(f"Docker validation failed: {e}")
            return False
            
    def validate_environment_file(self) -> Dict[str, Any]:
        """Validate .env file exists and contains required variables."""
        env_file = self.project_root / ".env"
        env_example = self.project_root / ".env.example"
        
        validation_result = {
            "exists": env_file.exists(),
            "missing_vars": [],
            "validation_errors": []
        }
        
        if not env_file.exists():
            validation_result["validation_errors"].append(".env file does not exist")
            return validation_result
            
        # Load existing .env
        env_vars = {}
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key] = value
        except Exception as e:
            validation_result["validation_errors"].append(f"Error reading .env file: {e}")
            return validation_result
            
        # Check required variables from .env.example
        required_vars = [
            "N8N_ENCRYPTION_KEY", "N8N_USER_MANAGEMENT_JWT_SECRET",
            "POSTGRES_PASSWORD", "JWT_SECRET", "ANON_KEY", "SERVICE_ROLE_KEY",
            "DASHBOARD_USERNAME", "DASHBOARD_PASSWORD", "POOLER_TENANT_ID",
            "NEO4J_AUTH", "CLICKHOUSE_PASSWORD", "MINIO_ROOT_PASSWORD",
            "LANGFUSE_SALT", "NEXTAUTH_SECRET", "ENCRYPTION_KEY"
        ]
        
        for var in required_vars:
            if var not in env_vars or not env_vars[var] or env_vars[var] in ['super-secret-key', 'your-super-secret-and-long-postgres-password']:
                validation_result["missing_vars"].append(var)
                
        return validation_result
        
    def create_env_file(self, force: bool = False) -> bool:
        """Create or update .env file from .env.example with generated secrets."""
        env_file = self.project_root / ".env"
        env_example = self.project_root / ".env.example"
        
        if env_file.exists() and not force:
            self.logger.info(".env file already exists. Use --force to overwrite.")
            return True
            
        if not env_example.exists():
            self.logger.error(".env.example file not found")
            return False
            
        self.logger.info("Creating .env file with generated secrets...")
        
        try:
            with open(env_example, 'r') as f:
                content = f.read()
                
            # Generate secrets for required variables
            secrets_map = {
                "N8N_ENCRYPTION_KEY": self.generate_hex_secret(32),
                "N8N_USER_MANAGEMENT_JWT_SECRET": self.generate_hex_secret(32),
                "POSTGRES_PASSWORD": self.generate_secret(32),
                "JWT_SECRET": self.generate_hex_secret(64),
                "ANON_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0",
                "SERVICE_ROLE_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU",
                "DASHBOARD_USERNAME": "supabase",
                "DASHBOARD_PASSWORD": self.generate_secret(24),
                "POOLER_TENANT_ID": "1000",
                "NEO4J_AUTH": f"neo4j/{self.generate_secret(16)}",
                "CLICKHOUSE_PASSWORD": self.generate_secret(32),
                "MINIO_ROOT_PASSWORD": self.generate_secret(32),
                "LANGFUSE_SALT": self.generate_secret(32),
                "NEXTAUTH_SECRET": self.generate_hex_secret(32),
                "ENCRYPTION_KEY": self.generate_hex_secret(32)
            }
            
            # Set Let's Encrypt email (prompt user or use env/arg)
            letsencrypt_email = os.environ.get("LETSENCRYPT_EMAIL")
            if not letsencrypt_email:
                # Prompt user for email, allow blank (will comment out in .env)
                print("Enter your email address for Let's Encrypt certificate notifications (leave blank to skip):")
                letsencrypt_email = input("LETSENCRYPT_EMAIL: ").strip()
            if letsencrypt_email:
                content = content.replace("# LETSENCRYPT_EMAIL=blaine.winslow@gmail.com", f"LETSENCRYPT_EMAIL={letsencrypt_email}")
            else:
                # Leave commented out, remind user to update
                content = content.replace("# LETSENCRYPT_EMAIL=blaine.winslow@gmail.com", "# LETSENCRYPT_EMAIL=your@email.com  # <-- Please update before deployment")
            for key, value in secrets_map.items():
                if key == "NEO4J_AUTH":
                    content = content.replace("NEO4J_AUTH=neo4j/password", f"NEO4J_AUTH={value}")
                elif "super-secret-key" in content:
                    content = content.replace("super-secret-key", value, 1)
                elif "generate-with-openssl" in content:
                    content = content.replace("generate-with-openssl", value)
                elif "your-super-secret-and-long-postgres-password" in content:
                    content = content.replace("your-super-secret-and-long-postgres-password", value)
                elif "your-super-secret-jwt-token-with-at-least-32-characters-long" in content:
                    content = content.replace("your-super-secret-jwt-token-with-at-least-32-characters-long", value)
                elif "this_password_is_insecure_and_should_be_updated" in content:
                    content = content.replace("this_password_is_insecure_and_should_be_updated", value)
                elif "your-tenant-id" in content:
                    content = content.replace("your-tenant-id", value)
                else:
                    # Generic replacement for any remaining placeholder
                    content = content.replace(f"{key}=", f"{key}={value}")
                    
            with open(env_file, 'w') as f:
                f.write(content)
                
            self.logger.info(f"Successfully created .env file with generated secrets")
            self.logger.info("IMPORTANT: Review and customize the generated .env file as needed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create .env file: {e}")
            return False
            
    def clone_supabase_repo(self):
        """Clone the Supabase repository using sparse checkout if not already present."""
        supabase_dir = self.project_root / "supabase"
        
        if supabase_dir.exists():
            self.logger.info("Supabase repository already exists, updating...")
            try:
                self.run_command(["git", "pull"], cwd=str(supabase_dir))
            except subprocess.CalledProcessError:
                self.logger.warning("Failed to update Supabase repo, continuing with existing version")
        else:
            self.logger.info("Cloning Supabase repository...")
            self.run_command([
                "git", "clone", "--filter=blob:none", "--no-checkout",
                SUPABASE_REPO_URL
            ])
            
            self.run_command(["git", "sparse-checkout", "init", "--cone"], cwd="supabase")
            self.run_command(["git", "sparse-checkout", "set", "docker"], cwd="supabase")
            self.run_command(["git", "checkout", "master"], cwd="supabase")
            
    def prepare_supabase_env(self):
        """Copy .env to supabase/docker/.env for Supabase services."""
        env_source = self.project_root / ".env"
        env_target = self.project_root / "supabase" / "docker" / ".env"
        
        if not env_source.exists():
            raise FileNotFoundError("Root .env file not found. Run 'init' command first.")
            
        self.logger.info("Copying .env to supabase/docker/.env...")
        env_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(env_source, env_target)
        
    def setup_searxng(self):
        """Set up SearXNG configuration with secret key generation."""
        self.logger.info("Setting up SearXNG configuration...")
        
        settings_path = self.project_root / "searxng" / "settings.yml"
        settings_base_path = self.project_root / "searxng" / "settings-base.yml"
        
        if not settings_base_path.exists():
            self.logger.warning(f"SearXNG base settings not found at {settings_base_path}")
            return
            
        if not settings_path.exists():
            self.logger.info("Creating SearXNG settings.yml from base template...")
            shutil.copyfile(settings_base_path, settings_path)
            
        # Generate and replace secret key
        try:
            secret_key = self.generate_hex_secret(32)
            with open(settings_path, 'r') as f:
                content = f.read()
            content = content.replace('ultrasecretkey', secret_key)
            with open(settings_path, 'w') as f:
                f.write(content)
            self.logger.info("SearXNG secret key generated successfully")
        except Exception as e:
            self.logger.error(f"Failed to generate SearXNG secret key: {e}")
            
    def get_service_health(self, service_name: str) -> Dict[str, Any]:
        """Get health status of a specific service."""
        try:
            result = self.run_command([
                "docker", "inspect", 
                "--format", "{{.State.Health.Status}}", 
                service_name
            ], capture_output=True)
            health_status = result.stdout.strip()
            
            # Get container status
            result = self.run_command([
                "docker", "inspect", 
                "--format", "{{.State.Status}}", 
                service_name
            ], capture_output=True)
            container_status = result.stdout.strip()
            
            return {
                "container_status": container_status,
                "health_status": health_status if health_status else "no-healthcheck",
                "healthy": health_status == "healthy" or (health_status == "" and container_status == "running")
            }
        except subprocess.CalledProcessError:
            return {
                "container_status": "not-found",
                "health_status": "unknown",
                "healthy": False
            }
            
    def wait_for_service_health(self, service_name: str, timeout: int = HEALTH_CHECK_TIMEOUT) -> bool:
        """Wait for a service to become healthy."""
        self.logger.info(f"Waiting for {service_name} to become healthy...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            health = self.get_service_health(service_name)
            if health["healthy"]:
                self.logger.info(f"{service_name} is healthy")
                return True
            time.sleep(5)
            
        self.logger.warning(f"{service_name} did not become healthy within {timeout}s")
        return False
        
    def get_running_services(self) -> List[str]:
        """Get list of running services for the project."""
        try:
            result = self.run_command([
                "docker", "compose", "-p", PROJECT_NAME, "ps", 
                "--format", "json"
            ], capture_output=True)
            
            services = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        service_data = json.loads(line)
                        if service_data.get('State') == 'running':
                            services.append(service_data.get('Service', service_data.get('Name', '')))
                    except json.JSONDecodeError:
                        continue
            return services
        except subprocess.CalledProcessError:
            return []
            
    def stop_services(self, profile: Optional[str] = None):
        """Stop all services for the project."""
        self.logger.info(f"Stopping services for project '{PROJECT_NAME}'...")
        
        cmd = ["docker", "compose", "-p", PROJECT_NAME]
        if profile and profile != "none":
            cmd.extend(["--profile", profile])
        cmd.extend(["-f", "docker-compose.yml", "down"])
        
        try:
            self.run_command(cmd)
            self.logger.info("Services stopped successfully")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to stop services: {e}")
            
    def start_supabase(self, environment: Optional[str] = None):
        """Start Supabase services."""
        self.logger.info("Starting Supabase services...")
        
        cmd = ["docker", "compose", "-p", PROJECT_NAME, "-f", "supabase/docker/docker-compose.yml"]
        if environment == "public":
            cmd.extend(["-f", "docker-compose.override.public.supabase.yml"])
        cmd.extend(["up", "-d"])
        
        self.run_command(cmd)
        
    def start_local_ai(self, profile: Optional[str] = None, environment: Optional[str] = None):
        """Start local AI services."""
        self.logger.info("Starting local AI services...")
        
        cmd = ["docker", "compose", "-p", PROJECT_NAME]
        if profile and profile != "none":
            cmd.extend(["--profile", profile])
        cmd.extend(["-f", "docker-compose.yml"])
        
        if environment == "private":
            cmd.extend(["-f", "docker-compose.override.private.yml"])
        elif environment == "public":
            cmd.extend(["-f", "docker-compose.override.public.yml"])
            
        cmd.extend(["up", "-d"])
        self.run_command(cmd)
        
    def get_service_logs(self, service: Optional[str] = None, since: str = "1h", 
                        follow: bool = False, tail: int = 100) -> None:
        """Get logs from services."""
        cmd = ["docker", "compose", "-p", PROJECT_NAME, "logs"]
        
        if since:
            cmd.extend(["--since", since])
        if follow:
            cmd.append("-f")
        if tail:
            cmd.extend(["--tail", str(tail)])
        if service:
            cmd.append(service)
            
        try:
            if follow:
                self.logger.info("Following logs (Ctrl+C to stop)...")
                self.run_command(cmd)
            else:
                result = self.run_command(cmd, capture_output=True)
                print(result.stdout)
        except KeyboardInterrupt:
            self.logger.info("Log following stopped")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to get logs: {e}")
            
    def run_diagnostics(self) -> Dict[str, Any]:
        """Run comprehensive diagnostics on the deployment."""
        self.logger.info("Running comprehensive diagnostics...")
        
        diagnostics = {
            "timestamp": datetime.now().isoformat(),
            "docker_validation": False,
            "environment_validation": {},
            "service_health": {},
            "connectivity_tests": {},
            "supabase_tests": {},
            "overall_status": "unknown"
        }
        
        # Docker validation
        diagnostics["docker_validation"] = self.validate_docker_installation()
        
        # Environment validation
        diagnostics["environment_validation"] = self.validate_environment_file()
        
        # Service health checks
        services = self.get_running_services()
        for service in services:
            diagnostics["service_health"][service] = self.get_service_health(service)
            
        # Basic connectivity tests
        self.logger.info("Running connectivity tests...")
        connectivity_tests = {}
        
        # Test key service endpoints
        endpoints = {
            "n8n": "http://localhost:5678",
            "open-webui": "http://localhost:8080", 
            "flowise": "http://localhost:3001",
            "langfuse": "http://localhost:3000",
            "supabase": "http://localhost:8000"
        }
        
        for service, url in endpoints.items():
            try:
                import urllib.request
                urllib.request.urlopen(url, timeout=10)
                connectivity_tests[service] = {"status": "accessible", "url": url}
            except Exception as e:
                connectivity_tests[service] = {"status": "inaccessible", "url": url, "error": str(e)}
                
        diagnostics["connectivity_tests"] = connectivity_tests
        
        # Determine overall status
        healthy_services = sum(1 for health in diagnostics["service_health"].values() if health["healthy"])
        total_services = len(diagnostics["service_health"])
        
        if diagnostics["docker_validation"] and total_services > 0 and healthy_services == total_services:
            diagnostics["overall_status"] = "healthy"
        elif healthy_services > 0:
            diagnostics["overall_status"] = "partial"
        else:
            diagnostics["overall_status"] = "unhealthy"
            
        # Save diagnostics to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        diag_file = Path(LOGS_DIR) / f"diagnostics_{timestamp}.json"
        with open(diag_file, 'w') as f:
            json.dump(diagnostics, f, indent=2)
            
        self.logger.info(f"Diagnostics saved to {diag_file}")
        
        return diagnostics
        
    def print_service_status(self):
        """Print current status of all services."""
        services = self.get_running_services()
        
        print("\n" + "="*50)
        print("SERVICE STATUS")
        print("="*50)
        
        if not services:
            print("No running services found")
            return
            
        for service in services:
            health = self.get_service_health(service)
            status_icon = "✅" if health["healthy"] else "❌"
            print(f"{status_icon} {service:<20} {health['container_status']:<10} {health['health_status']}")
            
        print("\nKey Service URLs:")
        print("- n8n: http://localhost:5678")
        print("- Open WebUI: http://localhost:8080")
        print("- Flowise: http://localhost:3001")
        print("- Langfuse: http://localhost:3000")
        print("- Supabase: http://localhost:8000")
        print("="*50)
        
    def deploy_remote(self, host: str, user: str, ssh_key: Optional[str] = None, 
                     domain: Optional[str] = None, dry_run: bool = False) -> bool:
        """Deploy to remote server via SSH."""
        self.logger.info(f"{'[DRY RUN] ' if dry_run else ''}Deploying to {user}@{host}")
        
        if dry_run:
            self.logger.info("Dry run mode - no actual changes will be made")
            
        # Prepare SSH command
        ssh_cmd = ["ssh"]
        if ssh_key:
            ssh_cmd.extend(["-i", ssh_key])
        ssh_cmd.extend(["-o", "StrictHostKeyChecking=no", f"{user}@{host}"])
        
        try:
            # Test SSH connectivity
            test_cmd = ssh_cmd + ["echo", "SSH connection successful"]
            if not dry_run:
                self.run_command(test_cmd, timeout=SSH_TIMEOUT)
            self.logger.info("SSH connectivity verified")
            
            # Check/install Docker
            docker_check = ssh_cmd + ["which", "docker"]
            try:
                if not dry_run:
                    self.run_command(docker_check, capture_output=True)
                self.logger.info("Docker found on remote server")
            except subprocess.CalledProcessError:
                self.logger.info("Installing Docker on remote server...")
                if not dry_run:
                    install_docker = ssh_cmd + [
                        "curl -fsSL https://get.docker.com | sh && sudo usermod -aG docker $USER"
                    ]
                    self.run_command(install_docker)
                    
            # Check/install Docker Compose
            compose_check = ssh_cmd + ["docker", "compose", "version"]
            try:
                if not dry_run:
                    self.run_command(compose_check, capture_output=True)
                self.logger.info("Docker Compose found on remote server")
            except subprocess.CalledProcessError:
                self.logger.info("Installing Docker Compose on remote server...")
                if not dry_run:
                    install_compose = ssh_cmd + ["""
                        DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d'"' -f4) &&
                        sudo curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-linux-x86_64" -o /usr/local/bin/docker-compose &&
                        sudo chmod +x /usr/local/bin/docker-compose
                    """]
                    self.run_command(install_compose)
                    
            # Create remote directory
            remote_dir = f"/home/{user}/local-ai-packaged"
            if not dry_run:
                mkdir_cmd = ssh_cmd + ["mkdir", "-p", remote_dir]
                self.run_command(mkdir_cmd)
                
            # Copy files to remote
            self.logger.info("Copying files to remote server...")
            files_to_copy = [
                "docker-compose.yml",
                "docker-compose.override.private.yml", 
                "docker-compose.override.public.yml",
                "docker-compose.override.public.supabase.yml",
                "start_services.py",
                ".env",
                "Caddyfile",
                "searxng/",
                "n8n/",
                "caddy-addon/",
                "flowise/"
            ]
            
            for file_path in files_to_copy:
                if Path(file_path).exists():
                    if not dry_run:
                        if Path(file_path).is_dir():
                            self.run_command(["rsync", "-avz", f"{file_path}/", f"{user}@{host}:{remote_dir}/{file_path}/"])
                        else:
                            self.run_command(["scp"] + (["-i", ssh_key] if ssh_key else []) + [file_path, f"{user}@{host}:{remote_dir}/"])
                    self.logger.info(f"Copied {file_path}")
                    
            # Configure domain and hostnames for remote deployment
            if domain and not dry_run:
                self.logger.info(f"Configuring domain {domain} for remote deployment...")
                env_config_cmd = ssh_cmd + [f'''cd {remote_dir} && 
                    sed -i 's/^# N8N_HOSTNAME=.*/N8N_HOSTNAME=n8n.{domain}/' .env &&
                    sed -i 's/^# WEBUI_HOSTNAME=.*/WEBUI_HOSTNAME=openwebui.{domain}/' .env &&
                    sed -i 's/^# FLOWISE_HOSTNAME=.*/FLOWISE_HOSTNAME=flowise.{domain}/' .env &&
                    sed -i 's/^# SUPABASE_HOSTNAME=.*/SUPABASE_HOSTNAME=supabase.{domain}/' .env &&
                    sed -i 's/^# LANGFUSE_HOSTNAME=.*/LANGFUSE_HOSTNAME=langfuse.{domain}/' .env &&
                    sed -i 's/^# NEO4J_HOSTNAME=.*/NEO4J_HOSTNAME=neo4j.{domain}/' .env &&
                    sed -i 's/^LETSENCRYPT_EMAIL=.*/LETSENCRYPT_EMAIL=blaine.winslow@gmail.com/' .env
                ''']
                self.run_command(env_config_cmd)
                self.logger.info("Domain configuration completed")
                    
            # Run deployment on remote
            self.logger.info("Starting services on remote server...")
            if not dry_run:
                deploy_cmd = ssh_cmd + [f"cd {remote_dir} && python3 start_services.py up --environment public"]
                self.run_command(deploy_cmd)
                
            self.logger.info("Remote deployment completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Remote deployment failed: {e}")
            return False
            
    def destroy_remote(self, host: str, user: str, ssh_key: Optional[str] = None, 
                      confirm: bool = False) -> bool:
        """Destroy remote deployment."""
        if not confirm:
            self.logger.warning("Remote destruction requires confirmation. Use --confirm flag.")
            return False
            
        self.logger.info(f"Destroying remote deployment on {user}@{host}")
        
        ssh_cmd = ["ssh"]
        if ssh_key:
            ssh_cmd.extend(["-i", ssh_key])
        ssh_cmd.extend(["-o", "StrictHostKeyChecking=no", f"{user}@{host}"])
        
        try:
            remote_dir = f"/home/{user}/local-ai-packaged"
            
            # Stop services
            stop_cmd = ssh_cmd + [f"cd {remote_dir} && python3 start_services.py down"]
            self.run_command(stop_cmd)
            
            # Remove directory
            remove_cmd = ssh_cmd + ["rm", "-rf", remote_dir]
            self.run_command(remove_cmd)
            
            self.logger.info("Remote deployment destroyed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to destroy remote deployment: {e}")
            return False

def main():
    """Main entry point for the orchestration script."""
    parser = argparse.ArgumentParser(
        description='Local AI Package Orchestration Script',
        epilog='For more information, see README.md'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize environment and .env file')
    init_parser.add_argument('--force', action='store_true', help='Force overwrite existing .env')
    
    # Up command  
    up_parser = subparsers.add_parser('up', help='Start all services')
    up_parser.add_argument('--profile', choices=['cpu', 'gpu-nvidia', 'gpu-amd', 'none'], 
                          default='cpu', help='Profile to use (default: cpu)')
    up_parser.add_argument('--environment', choices=['private', 'public'], 
                          default='private', help='Environment type (default: private)')
    up_parser.add_argument('--no-cache', action='store_true', help='Build without cache')
    
    # Down command
    down_parser = subparsers.add_parser('down', help='Stop all services')
    down_parser.add_argument('--profile', choices=['cpu', 'gpu-nvidia', 'gpu-amd', 'none'], 
                            help='Profile used when starting')
    down_parser.add_argument('--volumes', action='store_true', help='Remove volumes as well')
    
    # Restart command
    restart_parser = subparsers.add_parser('restart', help='Restart services')
    restart_parser.add_argument('--profile', choices=['cpu', 'gpu-nvidia', 'gpu-amd', 'none'], 
                               default='cpu', help='Profile to use (default: cpu)')
    restart_parser.add_argument('--environment', choices=['private', 'public'], 
                               default='private', help='Environment type (default: private)')
    
    # Logs command
    logs_parser = subparsers.add_parser('logs', help='View service logs')
    logs_parser.add_argument('service', nargs='?', help='Specific service to show logs for')
    logs_parser.add_argument('--since', default='1h', help='Show logs since (default: 1h)')
    logs_parser.add_argument('--follow', '-f', action='store_true', help='Follow log output')
    logs_parser.add_argument('--tail', type=int, default=100, help='Number of lines to show (default: 100)')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show service status and health')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Run diagnostics and tests')
    test_parser.add_argument('--output', help='Output file for test results')
    
    # Deploy-remote command
    deploy_parser = subparsers.add_parser('deploy-remote', help='Deploy to remote server')
    deploy_parser.add_argument('host', help='Remote host address')
    deploy_parser.add_argument('--user', default='root', help='SSH user (default: root)')
    deploy_parser.add_argument('--ssh-key', help='SSH private key file')
    deploy_parser.add_argument('--domain', help='Domain for HTTPS setup')
    deploy_parser.add_argument('--dry-run', action='store_true', help='Show what would be done')
    
    # Destroy-remote command
    destroy_parser = subparsers.add_parser('destroy-remote', help='Destroy remote deployment')
    destroy_parser.add_argument('host', help='Remote host address')
    destroy_parser.add_argument('--user', default='root', help='SSH user (default: root)')
    destroy_parser.add_argument('--ssh-key', help='SSH private key file')
    destroy_parser.add_argument('--confirm', action='store_true', help='Confirm destruction')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
        
    orchestrator = ServiceOrchestrator()
    
    try:
        if args.command == 'init':
            # Validate Docker first
            if not orchestrator.validate_docker_installation():
                orchestrator.logger.error("Docker validation failed. Please install Docker and Docker Compose.")
                return 1
                
            # Create .env file
            if not orchestrator.create_env_file(force=args.force):
                return 1
                
            orchestrator.logger.info("Initialization completed successfully")
            orchestrator.logger.info("Next steps:")
            orchestrator.logger.info("1. Review and customize the generated .env file")
            orchestrator.logger.info("2. Run 'python start_services.py up' to start services")
            
        elif args.command == 'up':
            # Validate prerequisites
            if not orchestrator.validate_docker_installation():
                orchestrator.logger.error("Docker validation failed")
                return 1
                
            env_validation = orchestrator.validate_environment_file()
            if not env_validation["exists"]:
                orchestrator.logger.error(".env file not found. Run 'init' command first.")
                return 1
            if env_validation["missing_vars"]:
                orchestrator.logger.error(f"Missing required environment variables: {', '.join(env_validation['missing_vars'])}")
                return 1
                
            # Setup and start services
            orchestrator.clone_supabase_repo()
            orchestrator.prepare_supabase_env()
            orchestrator.setup_searxng()
            
            # Stop existing services
            orchestrator.stop_services(args.profile)
            
            # Start services
            orchestrator.start_supabase(args.environment)
            orchestrator.logger.info("Waiting for Supabase to initialize...")
            time.sleep(10)
            
            orchestrator.start_local_ai(args.profile, args.environment)
            
            # Wait for key services and print status
            time.sleep(5)
            orchestrator.print_service_status()
            
        elif args.command == 'down':
            orchestrator.stop_services(args.profile)
            if args.volumes:
                orchestrator.logger.info("Removing volumes...")
                orchestrator.run_command([
                    "docker", "compose", "-p", PROJECT_NAME, 
                    "down", "--volumes"
                ])
                
        elif args.command == 'restart':
            orchestrator.logger.info("Restarting services...")
            orchestrator.stop_services(args.profile)
            time.sleep(3)
            
            orchestrator.start_supabase(args.environment)
            time.sleep(10)
            orchestrator.start_local_ai(args.profile, args.environment)
            
            time.sleep(5)
            orchestrator.print_service_status()
            
        elif args.command == 'logs':
            orchestrator.get_service_logs(
                service=args.service,
                since=args.since,
                follow=args.follow,
                tail=args.tail
            )
            
        elif args.command == 'status':
            orchestrator.print_service_status()
            
        elif args.command == 'test':
            results = orchestrator.run_diagnostics()
            
            print("\n" + "="*50)
            print("DIAGNOSTIC RESULTS")
            print("="*50)
            print(f"Overall Status: {results['overall_status'].upper()}")
            print(f"Docker: {'✅' if results['docker_validation'] else '❌'}")
            print(f"Environment: {'✅' if results['environment_validation']['exists'] else '❌'}")
            
            if results['environment_validation']['missing_vars']:
                print(f"Missing variables: {', '.join(results['environment_validation']['missing_vars'])}")
                
            print(f"\nService Health ({len([h for h in results['service_health'].values() if h['healthy']])}/{len(results['service_health'])} healthy):")
            for service, health in results['service_health'].items():
                status_icon = "✅" if health['healthy'] else "❌"
                print(f"  {status_icon} {service}")
                
            print(f"\nConnectivity Tests:")
            for service, test in results['connectivity_tests'].items():
                status_icon = "✅" if test['status'] == 'accessible' else "❌"
                print(f"  {status_icon} {service}: {test['url']}")
                
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(results, f, indent=2)
                orchestrator.logger.info(f"Detailed results saved to {args.output}")
                
            return 0 if results['overall_status'] in ['healthy', 'partial'] else 1
            
        elif args.command == 'deploy-remote':
            success = orchestrator.deploy_remote(
                host=args.host,
                user=args.user,
                ssh_key=args.ssh_key,
                domain=args.domain,
                dry_run=args.dry_run
            )
            return 0 if success else 1
            
        elif args.command == 'destroy-remote':
            success = orchestrator.destroy_remote(
                host=args.host,
                user=args.user,
                ssh_key=args.ssh_key,
                confirm=args.confirm
            )
            return 0 if success else 1
            
    except KeyboardInterrupt:
        orchestrator.logger.info("Operation cancelled by user")
        return 1
    except Exception as e:
        orchestrator.logger.error(f"Unexpected error: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())