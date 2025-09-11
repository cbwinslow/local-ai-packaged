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

def generate_hex_secret_openssl():
    """Generate a secure random hex secret using openssl rand -hex 32"""
    try:
        result = subprocess.run(['openssl', 'rand', '-hex', '32'], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback to Python secrets if openssl is not available
        return secrets.token_hex(32)

def generate_jwt_secret():
    """Generate a JWT secret - at least 32 characters as per Supabase docs"""
    # Per .env.example: "your-super-secret-jwt-token-with-at-least-32-characters-long"
    # Use openssl for consistency with other secrets
    try:
        result = subprocess.run(['openssl', 'rand', '-hex', '32'], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback to Python secrets if openssl is not available
        return secrets.token_hex(32)

def generate_jwt_keys(jwt_secret):
    """Generate ANON_KEY and SERVICE_ROLE_KEY based on JWT_SECRET"""
    import base64
    import json
    import hmac
    import hashlib
    
    header = {
        'alg': 'HS256',
        'typ': 'JWT'
    }
    
    anon_payload = {
        'role': 'anon',
        'iss': 'supabase',
        'iat': 1641769200,
        'exp': 1799535600
    }
    
    service_payload = {
        'role': 'service_role', 
        'iss': 'supabase',
        'iat': 1641769200,
        'exp': 1799535600
    }
    
    def encode_jwt(payload, secret):
        # Encode header and payload
        header_encoded = base64.urlsafe_b64encode(json.dumps(header, separators=(',', ':')).encode()).decode().rstrip('=')
        payload_encoded = base64.urlsafe_b64encode(json.dumps(payload, separators=(',', ':')).encode()).decode().rstrip('=')
        
        # Create signature
        message = f'{header_encoded}.{payload_encoded}'
        signature = hmac.new(secret.encode(), message.encode(), hashlib.sha256).digest()
        signature_encoded = base64.urlsafe_b64encode(signature).decode().rstrip('=')
        
        return f'{header_encoded}.{payload_encoded}.{signature_encoded}'
    
    anon_key = encode_jwt(anon_payload, jwt_secret)
    service_key = encode_jwt(service_payload, jwt_secret)
    
    return anon_key, service_key

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

def setup_environment(args=None):
    """Setup environment configuration"""
    print("\n📝 Setting up environment configuration...")
    
    env_path = ".env"
    env_example_path = ".env.example"
    
    if os.path.exists(env_path):
        if args and args.non_interactive:
            print("✅ Using existing .env file")
            return env_path
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
    
    print("\n🔐 Generating secure secrets following .env.example instructions...")
    
    # Generate JWT secret first using openssl as per documentation
    jwt_secret = generate_jwt_secret()
    anon_key, service_role_key = generate_jwt_keys(jwt_secret)
    
    # Generate secrets using openssl rand -hex 32 as specified in .env.example
    secrets_map = {
        'N8N_ENCRYPTION_KEY': generate_hex_secret_openssl(),
        'N8N_USER_MANAGEMENT_JWT_SECRET': generate_hex_secret_openssl(),
        'POSTGRES_PASSWORD': generate_secret(32),
        'JWT_SECRET': jwt_secret,
        'ANON_KEY': anon_key,
        'SERVICE_ROLE_KEY': service_role_key,
        'DASHBOARD_USERNAME': 'admin',
        'DASHBOARD_PASSWORD': generate_secret(20),
        'POOLER_TENANT_ID': '1000',
        'NEO4J_AUTH': f'neo4j/{generate_secret(20)}',
        'CLICKHOUSE_PASSWORD': generate_secret(32),
        'MINIO_ROOT_PASSWORD': generate_secret(32),
        'LANGFUSE_SALT': generate_secret(32),
        'NEXTAUTH_SECRET': generate_secret(32),
        'ENCRYPTION_KEY': generate_hex_secret_openssl(),  # Use openssl as per .env.example
        'SECRET_KEY_BASE': generate_hex_secret_openssl(),
        'VAULT_ENC_KEY': generate_hex_secret_openssl(),
        'FLOWISE_USERNAME': 'admin',
        'FLOWISE_PASSWORD': generate_secret(20),
        'SEARXNG_SECRET_KEY': generate_secret(32),
        'KONG_DB_PASSWORD': generate_secret(32),
        'KONG_TOKEN_SECRET': generate_secret(64),
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
    
    # Handle production setup
    if args and (args.production or args.domain):
        production_setup = True
        email = args.email or "admin@example.com"
        base_domain = args.domain or "localhost"
    elif args and args.non_interactive:
        production_setup = False
        email = None
        base_domain = None
    else:
        # Ask for optional configurations
        print("\n🌐 Optional configurations (press Enter to skip):")
        production_setup = input("Are you setting up for production with custom domains? (y/N): ").lower() == 'y'
        email = None
        base_domain = None
    
    if production_setup:
        if not email:
            email = get_user_input("Email for Let's Encrypt SSL certificates", required=True)
        if not base_domain:
            base_domain = get_user_input("Base domain (e.g., yourdomain.com)", required=True)
        
        domain_configs = {
            'N8N_HOSTNAME': f'n8n.{base_domain}',
            'WEBUI_HOSTNAME': f'openwebui.{base_domain}',
            'FLOWISE_HOSTNAME': f'flowise.{base_domain}',
            'SUPABASE_HOSTNAME': f'supabase.{base_domain}',
            'LANGFUSE_HOSTNAME': f'langfuse.{base_domain}',
            'NEO4J_HOSTNAME': f'neo4j.{base_domain}',
            'GRAPHITE_HOSTNAME': f'graphite.{base_domain}',
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
    if not (args and args.non_interactive):
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
    import argparse
    
    parser = argparse.ArgumentParser(description='Install Local AI Package')
    parser.add_argument('--non-interactive', action='store_true',
                       help='Run in non-interactive mode with defaults')
    parser.add_argument('--production', action='store_true',
                       help='Set up for production with SSL')
    parser.add_argument('--domain', help='Base domain for production setup')
    parser.add_argument('--email', help='Email for Let\'s Encrypt certificates')
    
    args = parser.parse_args()
    
    print_banner()
    
    # Check if we're in the right directory
    if not os.path.exists("docker-compose.yml"):
        print("❌ Please run this script from the local-ai-packaged directory")
        sys.exit(1)
    
    try:
        check_requirements()
        install_dependencies()
        setup_directories()
        env_path = setup_environment(args)
        clone_agentic_rag()
        
        print(f"""
        ✅ Installation completed successfully!
        
        📋 Next steps:
        1. Review your configuration in {env_path}
        2. Run the services: python3 start_services.py
        3. Access the web interface at http://localhost (or your configured domain)
        
        📚 Services will be available at:
        - N8N: http://localhost/n8n
        - Open WebUI: http://localhost/openwebui
        - Flowise: http://localhost/flowise
        - Supabase: http://localhost/supabase
        - Langfuse: http://localhost/langfuse
        - Neo4j: http://localhost/neo4j
        - Graphite: http://localhost/graphite
        
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