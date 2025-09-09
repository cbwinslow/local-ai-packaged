#!/usr/bin/env python3
"""
start_services.py

Enhanced script that starts the complete Local AI Package stack including:
- Supabase for database and authentication
- Traefik for reverse proxy and SSL
- All AI services (N8N, Open WebUI, Flowise, etc.)
- Agentic Knowledge RAG Graph service
- Frontend configuration interface
"""

import os
import subprocess
import shutil
import time
import argparse
import platform
import sys
import requests
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a shell command and print it."""
    print(f"🔧 Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=cwd, check=True, capture_output=False)
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed with exit code {e.returncode}")
        raise

def check_docker():
    """Check if Docker is running"""
    try:
        subprocess.run(["docker", "info"], check=True, capture_output=True)
        print("✅ Docker is running")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker is not running or not accessible")
        print("Please start Docker and try again.")
        return False

def check_env_file():
    """Check if .env file exists"""
    if not os.path.exists(".env"):
        print("❌ .env file not found!")
        print("Please run the installer first: python3 install.py")
        return False
    print("✅ .env file found")
    return True

def clone_supabase_repo():
    """Clone the Supabase repository using sparse checkout if not already present."""
    if not os.path.exists("supabase"):
        print("📦 Cloning the Supabase repository...")
        run_command([
            "git", "clone", "--filter=blob:none", "--no-checkout",
            "https://github.com/supabase/supabase.git"
        ])
        
        os.chdir("supabase")
        run_command(["git", "sparse-checkout", "init", "--cone"])
        run_command(["git", "sparse-checkout", "set", "docker"])
        run_command(["git", "checkout", "master"])
        os.chdir("..")
        print("✅ Supabase repository cloned and configured")
    else:
        print("✅ Supabase repository already exists")

def prepare_supabase_env():
    """Copy .env to .env in supabase/docker."""
    env_path = os.path.join("supabase", "docker", ".env")
    env_example_path = os.path.join(".env")
    print("📋 Copying .env to supabase/docker...")
    shutil.copyfile(env_example_path, env_path)
    print("✅ Environment configured for Supabase")

def setup_traefik():
    """Set up Traefik configuration and directories"""
    print("🚦 Setting up Traefik...")
    
    # Create Traefik directories
    dirs = ["traefik/config", "traefik/logs", "traefik/letsencrypt"]
    for directory in dirs:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    # Set permissions for Let's Encrypt storage
    letsencrypt_path = Path("traefik/letsencrypt")
    if letsencrypt_path.exists():
        os.chmod(letsencrypt_path, 0o600)
    
    print("✅ Traefik configuration ready")

def setup_frontend():
    """Build the frontend if needed"""
    if not os.path.exists("frontend/node_modules"):
        print("🌐 Setting up frontend dependencies...")
        if shutil.which("npm"):
            try:
                run_command(["npm", "install"], cwd="frontend")
                print("✅ Frontend dependencies installed")
            except subprocess.CalledProcessError:
                print("⚠️  Frontend setup failed, continuing without it")
        else:
            print("⚠️  npm not found, skipping frontend setup")

def wait_for_service(url, service_name, max_attempts=30, delay=5):
    """Wait for a service to become available"""
    print(f"⏳ Waiting for {service_name} to become available...")
    
    for attempt in range(max_attempts):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code < 500:
                print(f"✅ {service_name} is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        if attempt < max_attempts - 1:
            print(f"   Attempt {attempt + 1}/{max_attempts}, retrying in {delay}s...")
            time.sleep(delay)
    
    print(f"⚠️  {service_name} did not become ready in time")
    return False

def stop_existing_containers(profile=None):
    print("🛑 Stopping and removing existing containers...")
    
    # Stop main services
    cmd = ["docker", "compose", "-p", "localai"]
    if profile and profile != "none":
        cmd.extend(["--profile", profile])
    cmd.extend(["-f", "docker-compose.yml", "down"])
    
    try:
        run_command(cmd)
    except subprocess.CalledProcessError:
        print("⚠️  Some containers may not have been running")

def start_kong():
    """Start Kong API Gateway"""
    print("🦍 Starting Kong API Gateway...")
    cmd = ["docker", "compose", "-p", "localai", "-f", "docker-compose.kong.yml", "up", "-d"]
    run_command(cmd)
    
    # Wait for Kong to be ready
    wait_for_service("http://localhost:8001/", "Kong Admin", max_attempts=15, delay=5)

def start_traefik():
    """Start Traefik reverse proxy"""
    print("🚦 Starting Traefik reverse proxy...")
    cmd = ["docker", "compose", "-p", "localai", "-f", "docker-compose.traefik.yml", "up", "-d"]
    run_command(cmd)
    
    # Wait for Traefik to be ready
    wait_for_service("http://localhost:8080/ping", "Traefik", max_attempts=10, delay=2)

def start_supabase(environment=None):
    """Start the Supabase services."""
    print("🗄️  Starting Supabase services...")
    cmd = ["docker", "compose", "-p", "localai", "-f", "supabase/docker/docker-compose.yml"]
    if environment and environment == "public":
        cmd.extend(["-f", "docker-compose.override.public.supabase.yml"])
    cmd.extend(["up", "-d"])
    run_command(cmd)
    
    # Wait for Supabase to be ready
    wait_for_service("http://localhost:8000/health", "Supabase", max_attempts=20, delay=10)

def start_local_ai(profile=None, environment=None):
    """Start the local AI services."""
    print("🤖 Starting Local AI services...")
    cmd = ["docker", "compose", "-p", "localai"]
    if profile and profile != "none":
        cmd.extend(["--profile", profile])
    cmd.extend(["-f", "docker-compose.yml"])
    if environment and environment == "private":
        cmd.extend(["-f", "docker-compose.override.private.yml"])
    if environment and environment == "public":
        cmd.extend(["-f", "docker-compose.override.public.yml"])
    cmd.extend(["up", "-d"])
    run_command(cmd)

def generate_searxng_secret_key():
    """Generate a secret key for SearXNG based on the current platform."""
    print("🔐 Generating SearXNG secret key...")
    
    env_file = ".env"
    if not os.path.exists(env_file):
        print("⚠️  .env file not found for SearXNG configuration")
        return
    
    # Generate a random secret key
    import secrets
    import string
    secret_key = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    
    # Read the .env file
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Update or add the SearXNG secret key
    updated = False
    for i, line in enumerate(lines):
        if line.startswith('SEARXNG_SECRET_KEY='):
            lines[i] = f'SEARXNG_SECRET_KEY={secret_key}\n'
            updated = True
            break
    
    if not updated:
        lines.append(f'SEARXNG_SECRET_KEY={secret_key}\n')
    
    # Write back the .env file
    with open(env_file, 'w') as f:
        f.writelines(lines)
    
    print("✅ SearXNG secret key generated")

def check_and_fix_docker_compose_for_searxng():
    """Check and modify docker-compose.yml for SearXNG first run."""
    docker_compose_path = "docker-compose.yml"
    if not os.path.exists(docker_compose_path):
        print(f"⚠️  Docker Compose file not found at {docker_compose_path}")
        return

    try:
        # Read the docker-compose.yml file
        with open(docker_compose_path, 'r') as file:
            content = file.read()

        # Default to first run
        is_first_run = True

        # Check if Docker is running and if the SearXNG container exists
        try:
            # Check if the SearXNG container is running
            container_check = subprocess.run(
                ["docker", "ps", "--filter", "name=searxng", "--format", "{{.Names}}"],
                capture_output=True, text=True, check=True
            )
            searxng_containers = container_check.stdout.strip().split('\n')

            # If SearXNG container is running, check inside for uwsgi.ini
            for container in searxng_containers:
                if container and 'searxng' in container:
                    # Check if uwsgi.ini exists inside the container
                    uwsgi_check = subprocess.run(
                        ["docker", "exec", container, "ls", "/etc/searxng/uwsgi.ini"],
                        capture_output=True, text=True
                    )
                    if uwsgi_check.returncode == 0:
                        is_first_run = False
                        print("✅ SearXNG has been initialized previously")
                        break

            if is_first_run:
                print("ℹ️  No running SearXNG container found - assuming first run")
        except Exception as e:
            print(f"⚠️  Error checking Docker container: {e} - assuming first run")

        # Handle cap_drop configuration based on first run status
        if is_first_run and "cap_drop: - ALL" in content:
            print("🔧 First run detected for SearXNG. Temporarily removing 'cap_drop: - ALL' directive...")
            # Temporarily comment out the cap_drop line
            modified_content = content.replace("cap_drop: - ALL", "# cap_drop: - ALL  # Temporarily commented out for first run")

            # Write the modified content back
            with open(docker_compose_path, 'w') as file:
                file.write(modified_content)

            print("ℹ️  Note: After the first run completes successfully, you should re-add 'cap_drop: - ALL' to docker-compose.yml for security reasons.")

        elif not is_first_run and "# cap_drop: - ALL  # Temporarily commented out for first run" in content:
            print("🔐 SearXNG has been initialized. Re-enabling 'cap_drop: - ALL' directive for security...")
            # Uncomment the cap_drop line
            modified_content = content.replace("# cap_drop: - ALL  # Temporarily commented out for first run", "cap_drop: - ALL")

            # Write the modified content back
            with open(docker_compose_path, 'w') as file:
                file.write(modified_content)

    except Exception as e:
        print(f"❌ Error checking/modifying docker-compose.yml for SearXNG: {e}")

def show_service_urls():
    """Display URLs for accessing services"""
    print("\n" + "="*60)
    print("🎉 Local AI Package is ready!")
    print("="*60)
    print("\n📱 Service Access URLs:")
    print("   🌐 Frontend Dashboard:  http://localhost")
    print("   🔧 N8N Workflows:      http://localhost/n8n")
    print("   💬 Open WebUI:         http://localhost/openwebui")
    print("   🔄 Flowise:            http://localhost/flowise")
    print("   🗄️  Supabase:           http://localhost/supabase")
    print("   📊 Langfuse:           http://localhost/langfuse")
    print("   🔍 SearXNG:            http://localhost/searxng")
    print("   📈 Neo4j Browser:      http://localhost/neo4j")
    print("   🧠 Agentic RAG:        http://localhost/agentic")
    print("   📊 Graphite:           http://localhost/graphite")
    print("   🚦 Traefik Dashboard:  http://localhost:8080")
    print("\n🔧 System Information:")
    print("   📊 All services are managed through Traefik")
    print("   🐳 Docker project name: localai")
    print("   📝 Logs: docker compose -p localai logs [service]")
    print("   🛑 Stop: docker compose -p localai down")
    print("\n💡 Getting Started:")
    print("   1. Visit the Frontend Dashboard to configure services")
    print("   2. Set up your first AI workflow in N8N")
    print("   3. Chat with your AI models in Open WebUI")
    print("   4. Monitor performance in Langfuse")
    print("="*60)

def main():
    parser = argparse.ArgumentParser(description='Start the enhanced Local AI Package with all services.')
    parser.add_argument('--profile', choices=['cpu', 'gpu-nvidia', 'gpu-amd', 'none'], default='cpu',
                      help='Profile to use for Docker Compose (default: cpu)')
    parser.add_argument('--environment', choices=['private', 'public'], default='private',
                      help='Environment to use for Docker Compose (default: private)')
    parser.add_argument('--api-gateway', choices=['traefik', 'kong'], default='traefik',
                      help='API Gateway to use (default: traefik)')
    parser.add_argument('--skip-build', action='store_true',
                      help='Skip building frontend and agentic services')
    args = parser.parse_args()

    print("🚀 Starting Local AI Package...")
    print(f"   Profile: {args.profile}")
    print(f"   Environment: {args.environment}")
    print(f"   API Gateway: {args.api_gateway}")
    
    # Pre-flight checks
    if not check_docker():
        sys.exit(1)
    
    if not check_env_file():
        sys.exit(1)

    try:
        # Setup and preparation
        clone_supabase_repo()
        prepare_supabase_env()
        setup_traefik()
        
        if not args.skip_build:
            setup_frontend()

        # Generate SearXNG secret key and check docker-compose.yml
        generate_searxng_secret_key()
        check_and_fix_docker_compose_for_searxng()

        # Stop existing containers
        stop_existing_containers(args.profile)

        # Start services in order
        if args.api_gateway == "kong":
            start_kong()
            time.sleep(10)  # Give Kong time to initialize
        else:
            start_traefik()
            time.sleep(5)  # Give Traefik time to initialize

        start_supabase(args.environment)
        time.sleep(15)  # Give Supabase more time to initialize

        start_local_ai(args.profile, args.environment)
        
        # Give services time to start
        print("⏳ Waiting for all services to start...")
        time.sleep(20)

        # Show access information
        show_service_urls()

    except KeyboardInterrupt:
        print("\n⚠️  Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Failed to start services: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Check Docker is running: docker info")
        print("   2. Check logs: docker compose -p localai logs")
        print("   3. Reset everything: docker compose -p localai down -v")
        sys.exit(1)

if __name__ == "__main__":
    main()