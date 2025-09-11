#!/usr/bin/env python3
"""
One-Click Deployment Script for Local AI Package
Supports both local and remote deployments with enhanced features
"""

import os
import sys
import subprocess
import argparse
import time
try:
    import requests
except ImportError:
    print("❌ The 'requests' library is required but not installed.")
    print("   Please install it by running: pip install requests")
    sys.exit(1)
from pathlib import Path

def print_banner():
    """Print deployment banner"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║         Local AI Package - One-Click Deployment             ║
    ║                                                              ║
    ║  Deploy locally or to remote servers with full automation   ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

def check_prerequisites():
    """Check if all prerequisites are met"""
    print("🔍 Checking prerequisites...")
    
    # Check Docker
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
        subprocess.run(["docker", "compose", "version"], check=True, capture_output=True)
        print("✅ Docker and Docker Compose are available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker or Docker Compose not found")
        return False
    
    # Check if we can connect to Docker daemon
    try:
        subprocess.run(["docker", "info"], check=True, capture_output=True)
        print("✅ Docker daemon is running")
    except subprocess.CalledProcessError:
        print("❌ Docker daemon is not running")
        return False
    
    return True

def run_installer():
    """Run the installation script"""
    print("📦 Running installer...")
    try:
        subprocess.run([sys.executable, "install.py"], check=True)
        print("✅ Installation completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
        return False

def deploy_local(args):
    """Deploy locally with specified options"""
    print("🏠 Starting local deployment...")
    
    cmd = [sys.executable, "start_services.py"]
    
    if args.profile:
        cmd.extend(["--profile", args.profile])
    
    if args.environment:
        cmd.extend(["--environment", args.environment])
    
    if args.api_gateway == "kong":
        cmd.extend(["--api-gateway", "kong"])
    
    if args.skip_build:
        cmd.append("--skip-build")
    
    try:
        subprocess.run(cmd, check=True)
        print("✅ Local deployment completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Local deployment failed: {e}")
        return False

def deploy_remote(args):
    """Deploy to remote server"""
    print("☁️  Starting remote deployment...")
    
    if not args.remote_host:
        print("❌ Remote host is required for remote deployment")
        return False
    
    # Create deployment package
    print("📦 Creating deployment package...")
    package_cmd = [
        "tar", "-czf", "/tmp/local-ai-package.tar.gz",
        "--exclude='.git'",
        "--exclude='node_modules'",
        "--exclude='*.log'",
        "--exclude='.env'",
        "."
    ]
    
    try:
        subprocess.run(package_cmd, check=True)
        print("✅ Deployment package created")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create package: {e}")
        return False
    
    # Copy to remote server
    remote_user = args.remote_user or "root"
    remote_path = args.remote_path or "/opt/local-ai-packaged"
    
    print(f"📤 Copying to {remote_user}@{args.remote_host}:{remote_path}")
    
    # Create remote directory
    ssh_cmd = [
        "ssh", f"{remote_user}@{args.remote_host}",
        f"mkdir -p {remote_path}"
    ]
    
    try:
        subprocess.run(ssh_cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create remote directory: {e}")
        return False
    
    # Copy files
    scp_cmd = [
        "scp", "/tmp/local-ai-package.tar.gz",
        f"{remote_user}@{args.remote_host}:{remote_path}/local-ai-package.tar.gz"
    ]
    
    try:
        subprocess.run(scp_cmd, check=True)
        print("✅ Files copied to remote server")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to copy files: {e}")
        return False
    
    # Extract and deploy on remote server
    print("🚀 Deploying on remote server...")
    
    remote_deploy_cmd = [
        "ssh", f"{remote_user}@{args.remote_host}",
        f"cd {remote_path} && "
        f"tar -xzf local-ai-package.tar.gz && "
        f"python3 install.py --non-interactive && "
        f"python3 start_services.py --environment public --profile {args.profile or 'cpu'}"
    ]
    
    try:
        subprocess.run(remote_deploy_cmd, check=True)
        print("✅ Remote deployment completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Remote deployment failed: {e}")
        return False

def health_check():
    """Perform health checks on deployed services"""
    print("🔍 Performing health checks...")
    
    services = [
        ("Traefik", "http://localhost:8080/ping"),
        ("Frontend", "http://localhost"),
        ("Supabase", "http://localhost/supabase"),
        ("N8N", "http://localhost/n8n"),
        ("Open WebUI", "http://localhost/openwebui"),
    ]
    
    all_healthy = True
    
    for service_name, url in services:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code < 500:
                print(f"✅ {service_name} is healthy")
            else:
                print(f"⚠️  {service_name} returned {response.status_code}")
                all_healthy = False
        except requests.exceptions.RequestException:
            print(f"❌ {service_name} is not responding")
            all_healthy = False
    
    return all_healthy

def show_deployment_info(args):
    """Show deployment information"""
    print("\n" + "="*60)
    print("🎉 Deployment completed!")
    print("="*60)
    
    if args.deployment_type == "local":
        print("\n📱 Local Access URLs:")
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
        
        if args.api_gateway == "kong":
            print("   🦍 Kong Admin:         http://localhost:8001")
            print("   🎯 Konga Dashboard:    http://localhost:1337")
    else:
        print(f"\n📱 Remote Access URLs (replace {args.remote_host}):")
        print(f"   🌐 Frontend Dashboard:  https://{args.remote_host}")
        print(f"   🔧 N8N Workflows:      https://{args.remote_host}/n8n")
        print(f"   💬 Open WebUI:         https://{args.remote_host}/openwebui")
        # ... add other services
    
    print("\n🔧 Management Commands:")
    print("   📊 Check logs:         docker compose -p localai logs")
    print("   🛑 Stop services:      docker compose -p localai down")
    print("   🔄 Restart services:   docker compose -p localai restart")
    print("   🧹 Clean up:           docker compose -p localai down -v")
    
    print("\n💡 Next Steps:")
    print("   1. Visit the Frontend Dashboard to configure services")
    print("   2. Set up your first AI workflow in N8N")
    print("   3. Chat with your AI models in Open WebUI")
    print("   4. Monitor performance in Langfuse and Graphite")
    print("="*60)

def main():
    """Main deployment function"""
    parser = argparse.ArgumentParser(description='One-click deployment for Local AI Package')
    
    # Deployment type
    parser.add_argument('deployment_type', choices=['local', 'remote'], 
                       help='Deployment type: local or remote')
    
    # Local deployment options
    parser.add_argument('--profile', choices=['cpu', 'gpu-nvidia', 'gpu-amd'], 
                       default='cpu', help='Hardware profile to use')
    parser.add_argument('--environment', choices=['private', 'public'], 
                       default='private', help='Environment configuration')
    parser.add_argument('--api-gateway', choices=['traefik', 'kong'], 
                       default='traefik', help='API Gateway to use')
    parser.add_argument('--skip-build', action='store_true', 
                       help='Skip building frontend and services')
    
    # Remote deployment options
    parser.add_argument('--remote-host', help='Remote host for deployment')
    parser.add_argument('--remote-user', default='root', help='Remote user')
    parser.add_argument('--remote-path', default='/opt/local-ai-packaged', 
                       help='Remote deployment path')
    
    # General options
    parser.add_argument('--skip-health-check', action='store_true',
                       help='Skip health checks after deployment')
    parser.add_argument('--non-interactive', action='store_true',
                       help='Run in non-interactive mode')
    
    args = parser.parse_args()
    
    print_banner()
    
    # Check if we're in the right directory
    if not os.path.exists("docker-compose.yml"):
        print("❌ Please run this script from the local-ai-packaged directory")
        sys.exit(1)
    
    try:
        # Prerequisites check
        if not check_prerequisites():
            sys.exit(1)
        
        # Run installer if needed
        if not os.path.exists(".env"):
            if not run_installer():
                sys.exit(1)
        
        # Deploy based on type
        if args.deployment_type == "local":
            success = deploy_local(args)
        else:
            success = deploy_remote(args)
        
        if not success:
            sys.exit(1)
        
        # Health check
        if not args.skip_health_check:
            print("\n⏳ Waiting for services to start...")
            time.sleep(30)
            if not health_check():
                print("⚠️  Some services may not be fully ready yet")
        
        # Show deployment info
        show_deployment_info(args)
        
    except KeyboardInterrupt:
        print("\n⚠️  Deployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()