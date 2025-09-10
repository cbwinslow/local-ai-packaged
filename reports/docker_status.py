#!/usr/bin/env python3.10
import subprocess
import json

def get_docker_status():
    try:
        result = subprocess.run(['docker', 'ps', '--format', 'json'], capture_output=True, text=True, check=True)
        containers = json.loads(result.stdout)
        print("Docker containers status:")
        for c in containers:
            print(f"  - {c['Names']}: {c['Status']}")
        return True
    except Exception as e:
        print(f"Docker status check failed: {e}")
        return False

def get_docker_compose_status():
    try:
        result = subprocess.run(['docker', 'compose', 'ps', '--services', '--format', 'json'], capture_output=True, text=True, check=True)
        services = json.loads(result.stdout)
        print("Docker Compose services status:")
        for s in services:
            print(f"  - {s}")
        return True
    except Exception as e:
        print(f"Docker Compose status check failed: {e}")
        return False

if __name__ == "__main__":
    get_docker_status()
    get_docker_compose_status()