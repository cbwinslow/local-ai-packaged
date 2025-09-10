#!/usr/bin/env python3.10
import subprocess
import json

def get_docker_status():
    try:
        result = subprocess.run(['docker', 'ps', '--format', 'json'], capture_output=True, text=True, check=True)
        containers_output = result.stdout.strip()
        if not containers_output:
            print("No running containers found.")
            return True

        containers = []
        for line in containers_output.split('\n'):
            line = line.strip()
            if line:
                try:
                    containers.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        print("Docker containers status:")
        for c in containers:
            if isinstance(c, dict):
                names = c.get('Names', 'Unknown')
                status = c.get('Status', 'Unknown')
                print(f"  - {names}: {status}")
        return True
    except Exception as e:
        print(f"Docker status check failed: {e}")
        return False

def get_docker_compose_status():
    try:
        result = subprocess.run(['docker', 'compose', 'ps', '--services'], capture_output=True, text=True, check=True)
        services = [s.strip() for s in result.stdout.strip().split('\n') if s.strip()]
        print("Docker Compose services status:")
        if not services:
            print("No services found in docker-compose.yml")
            return True

        for s in services:
            print(f"  - {s}")
        return True
    except Exception as e:
        print(f"Docker Compose status check failed: {e}")
        return False

if __name__ == "__main__":
    get_docker_status()
    get_docker_compose_status()
