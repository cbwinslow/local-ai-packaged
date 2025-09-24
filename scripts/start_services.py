#!/usr/bin/env python3
# Start/Stop Services Script for Local AI Packaged
# Usage: python3 scripts/start_services.py [start|stop|status] [--remote 100.90.23.59]
# Handles local and remote (SSH) Docker Compose for homelab deployment.

import subprocess
import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
COMPOSE_FILE = PROJECT_ROOT / "docker-compose.yml"

def run_command(cmd, cwd=PROJECT_ROOT, check=True):
    result = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result

def local_start():
    print("Starting services locally...")
    run_command("docker compose up -d", check=True)

def local_stop():
    print("Stopping services locally...")
    run_command("docker compose down -v", check=True)

def local_status():
    print("Service status:")
    run_command("docker compose ps", check=False)

def remote_start(ip):
    print(f"Starting services on remote server {ip}...")
    run_command(f"ssh {ip} 'cd /opt/local-ai-packaged && docker compose up -d'", check=True)

def remote_stop(ip):
    print(f"Stopping services on remote server {ip}...")
    run_command(f"ssh {ip} 'cd /opt/local-ai-packaged && docker compose down -v'", check=True)

def remote_status(ip):
    print(f"Service status on {ip}:")
    run_command(f"ssh {ip} 'cd /opt/local-ai-packaged && docker compose ps'", check=False)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/start_services.py [start|stop|status] [--remote IP]")
        sys.exit(1)
    
    action = sys.argv[1]
    remote = None
    if "--remote" in sys.argv:
        remote = sys.argv[sys.argv.index("--remote") + 1]
    
    if action == "start":
        if remote:
            remote_start(remote)
        else:
            local_start()
    elif action == "stop":
        if remote:
            remote_stop(remote)
        else:
            local_stop()
    elif action == "status":
        if remote:
            remote_status(remote)
        else:
            local_status()
    else:
        print("Invalid action. Use start, stop, or status.")
