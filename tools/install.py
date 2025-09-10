#!/usr/bin/env python3
"""
One-click installer for Local AI Package
Handles .env creation, secret generation, and initial setup
"""

import os
import sys
import subprocess
import secrets
import string
import shutil
import platform
import requests
from pathlib import Path

def print_banner():
    """Print installation banner"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║             Local AI Package - One-Click Installer          ║
    ║                                                              ║
    ║  This installer will set up all required configurations     ║
    ║  and generate secure secrets for your deployment.           ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

def check_requirements():
    """Check if required tools are installed"""
    print("🔍 Checking requirements...")
    
    # Check Docker
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
        print("✅ Docker is installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker is not installed or not accessible")
        print("Please install Docker: https://docs.docker.com/get-docker/")
        sys.exit(1)
    
    # Check Docker Compose
    try:
        subprocess.run(["docker", "compose", "version"], check=True, capture_output=True)
        print("✅ Docker Compose is installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker Compose is not installed or not accessible")
        sys.exit(1)
    
    # Check Git
    try:
        subprocess.run(["git", "--version"], check=True, capture_output=True)
        print("✅ Git is installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Git is not installed")
        print("Please install Git: https://git-scm.com/downloads")
        sys.exit(1)

def generate_secret(length=32):
    """Generate a secure random secret"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_hex_secret(length=32):
    """Generate a secure random hex secret"""
    return secrets.token_hex(length)

def generate_jwt_secret():
    """Generate a JWT secret with proper format"""
    # For JWT secrets, we need a base64url encoded secret
    import base64
    raw_secret = secrets.token_bytes(32)
    return base64.urlsafe_b64encode(raw_secret).decode('utf-8').rstrip('=')

def get_user_input(prompt, default=None, required=True):
    """Get user input with optional default"""
    if default:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "
    
    while True:
        value = input(prompt).strip()
        if value:
            return value
        elif default:
            return default
        elif not required:
            return ""
        else:
            print("This field is required. Please enter a value.")

def setup_environment():
    """Setup environment configuration"""
    print("\n📝 Setting up environment configuration...")
    
    env_path = ".env"
    env_example_path = ".env.example"
    
    if os.path.exists(env_path):
        overwrite = input(f"\n⚠️  {env_path} already exists. Overwrite? (y/N): ").lower()
        if overwrite != 'y':
            print("Keeping existing .env file. You may need to update it manually.")
            return env_path
    
    # Read .env.example
    if not os.path.exists(env_example_path):
        print(f"❌ {env_example_path} not found")
        sys.exit(1)
    
    with open(env_example_path, 'r') as f:
        env_content = f.read()
    
    print("\n🔐 Generating secure secrets...")
    
    # Generate secrets
    secrets_map = {
        'N8N_ENCRYPTION_KEY': generate_hex_secret(32),
        'N8N_USER_MANAGEMENT_JWT_SECRET': generate_hex_secret(32),
        'POSTGRES_PASSWORD': generate_secret(32),
        'JWT_SECRET': generate_jwt_secret(),
        'DASHBOARD_USERNAME': 'admin',
        'DASHBOARD_PASSWORD': generate_secret(20),
        'POOLER_TENANT_ID': '1000',
        'NEO4J_AUTH': f'neo4j/{generate_secret(20)}',
        'CLICKHOUSE_PASSWORD': generate_secret(32),
        'MINIO_ROOT_PASSWORD': generate_secret(32),
        'LANGFUSE_SALT': generate_secret(32),
        'NEXTAUTH_SECRET': generate_secret(32),
        'ENCRYPTION_KEY': generate_hex_secret(32),
        'SECRET_KEY_BASE': generate_hex_secret(64),
        'VAULT_ENC_KEY': generate_hex_secret(32),
    }
    
    # Replace secrets in env content
    for key, value in secrets_map.items():
        if f'{key}=' in env_content:
            # Find the line and replace the value
            lines = env_content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith(f'{key}='):
                    lines[i] = f'{key}={value}'
                    break
            env_content = '\n'.join(lines)
    
    # Ask for optional configurations
    print("\n🌐 Optional configurations (press Enter to skip):")
    
    # Domain configurations for production
    production_setup = input("Are you setting up for production with custom domains? (y/N): ").lower() == 'y'
    
    if production_setup:
        email = get_user_input("Email for Let's Encrypt SSL certificates", required=True)
        base_domain = get_user_input("Base domain (e.g., yourdomain.com)", required=True)
        
        domain_configs = {
            'N8N_HOSTNAME': f'n8n.{base_domain}',
            'WEBUI_HOSTNAME': f'openwebui.{base_domain}',
            'FLOWISE_HOSTNAME': f'flowise.{base_domain}',
            'SUPABASE_HOSTNAME': f'supabase.{base_domain}',
            'LANGFUSE_HOSTNAME': f'langfuse.{base_domain}',
            'NEO4J_HOSTNAME': f'neo4j.{base_domain}',
            'LETSENCRYPT_EMAIL': email,
        }
        
        for key, value in domain_configs.items():
            env_content = env_content.replace(f'# {key}=', f'{key}=')
            lines = env_content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith(f'{key}='):
                    lines[i] = f'{key}={value}'
                    break
            env_content = '\n'.join(lines)
    
    # Optional Google OAuth
    google_oauth = input("Configure Google OAuth for Supabase? (y/N): ").lower() == 'y'
    if google_oauth:
        google_client_id = get_user_input("Google Client ID", required=True)
        google_client_secret = get_user_input("Google Client Secret", required=True)
        google_redirect_uri = get_user_input("Google Redirect URI", f"http://localhost:8000/auth/v1/callback", required=True)
        
        google_configs = {
            'ENABLE_GOOGLE_SIGNUP': 'true',
            'GOOGLE_CLIENT_ID': google_client_id,
            'GOOGLE_CLIENT_SECRET': google_client_secret,
            'GOOGLE_REDIRECT_URI': google_redirect_uri,
        }
        
        for key, value in google_configs.items():
            env_content = env_content.replace(f'# {key}=', f'{key}={value}')
    
    # Write the .env file
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(f"✅ Generated {env_path} with secure secrets")
    return env_path

def clone_agentic_rag():
    """Clone agentic-knowledge-rag-graph from ottoman-agents repo"""
    print("\n📦 Setting up agentic-knowledge-rag-graph...")
    
    agentic_dir = "agentic-knowledge-rag-graph"
    
    if os.path.exists(agentic_dir):
        print(f"✅ {agentic_dir} already exists")
        return
    
    try:
        # Clone the specific folder using sparse checkout
        print("Cloning agentic-knowledge-rag-graph from ottoman-agents repository...")
        
        # Create a temporary directory for cloning
        temp_dir = "temp_ottoman_agents"
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        
        # Clone with sparse checkout
        subprocess.run([
            "git", "clone", "--filter=blob:none", "--sparse",
            "https://github.com/ottoman-org/ottoman-agents.git",
            temp_dir
        ], check=True)
        
        # Set up sparse checkout
        subprocess.run([
            "git", "-C", temp_dir, "sparse-checkout", "set",
            "agentic-knowledge-rag-graph"
        ], check=True)
        
        # Move the directory
        if os.path.exists(os.path.join(temp_dir, "agentic-knowledge-rag-graph")):
            shutil.move(os.path.join(temp_dir, "agentic-knowledge-rag-graph"), agentic_dir)
            print(f"✅ Successfully cloned {agentic_dir}")
        else:
            print(f"⚠️  agentic-knowledge-rag-graph not found in ottoman-agents repo")
        
        # Clean up
        shutil.rmtree(temp_dir)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to clone agentic-knowledge-rag-graph: {e}")
        print("You may need to add this manually from the ottoman-agents repository")

def setup_directories():
    """Create necessary directories"""
    print("\n📁 Creating necessary directories...")
    
    directories = [
        "shared",
        "neo4j/data",
        "neo4j/logs", 
        "neo4j/config",
        "neo4j/plugins",
        "supabase",
        "frontend",
        "traefik/config",
        "traefik/logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def install_dependencies():
    """Install any Python dependencies needed"""
    print("\n📦 Installing Python dependencies...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "requests", "pyyaml", "docker", "jinja2"
        ], check=True)
        print("✅ Python dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Failed to install some Python dependencies: {e}")
        print("You may need to install them manually: pip install requests pyyaml docker jinja2")

def main():
    """Main installation function"""
    print_banner()
    
    # Check if we're in the right directory
    if not os.path.exists("docker-compose.yml"):
        print("❌ Please run this script from the local-ai-packaged directory")
        sys.exit(1)
    
    try:
        check_requirements()
        install_dependencies()
        setup_directories()
        env_path = setup_environment()
        clone_agentic_rag()
        
        print(f"""
        ✅ Installation completed successfully!
        
        📋 Next steps:
        1. Review your configuration in {env_path}
        2. Run the services: python3 start_services.py
        3. Access the web interface at http://localhost (or your configured domain)
        
        📚 Services will be available at:
        - N8N: http://localhost:8001 (or your configured domain)
        - Open WebUI: http://localhost:8002
        - Flowise: http://localhost:8003  
        - Supabase: http://localhost:8005
        - Langfuse: http://localhost:8007
        - Neo4j: http://localhost:8008
        
        🔐 Important: Save your generated secrets in a secure location!
        """)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Installation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()