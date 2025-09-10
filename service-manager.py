#!/usr/bin/env python3
"""
Service Manager - Comprehensive container management system for legislative AI project
Handles service discovery, port management, health monitoring, and auto-configuration
"""

import subprocess
import json
import yaml
import psutil
import socket
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Service:
    name: str
    docker_name: str
    port: int
    status: str = "unknown"
    health: str = "unknown"
    url: Optional[str] = None

    @property
    def is_running(self) -> bool:
        return self.status in ['running', 'healthy']

    @property
    def is_healthy(self) -> bool:
        return self.health == 'healthy'

class ServiceManager:
    def __init__(self, compose_file: str = "docker-compose.yml"):
        self.compose_file = compose_file
        self.services: Dict[str, Service] = {}
        self.port_mappings: Dict[int, str] = {}
        self.discover_services()

    def discover_services(self):
        """Discover services from docker-compose.yml and running containers"""
        with open(self.compose_file, 'r') as f:
            compose_data = yaml.safe_load(f)

        if 'services' in compose_data:
            for service_name, config in compose_data['services'].items():
                if 'ports' in config:
                    port_info = config['ports'][0]  # Take first port
                    if isinstance(port_info, str):
                        if ':' in port_info:
                            external_port = port_info.split(':')[0]
                            port = int(external_port)
                        else:
                            port = int(port_info)
                    else:
                        port = port_info.get('published', 3000)  # Default port

                    self.services[service_name] = Service(
                        name=service_name,
                        docker_name=f"local-ai-packaged-{service_name}-1",
                        port=port
                    )

        self.update_service_status()

    def update_service_status(self):
        """Update status of all discovered services"""
        try:
            result = subprocess.run(
                ['docker', 'ps', '--format', 'json', '--all'],
                capture_output=True, text=True, check=True
            )

            containers = []
            for line in result.stdout.strip().split('\n'):
                line = line.strip()
                if line:
                    try:
                        containers.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

            for container in containers:
                container_names = container.get('Names', '')
                if 'supabase' in container_names or 'local-ai-packaged' in container_names:
                    service_name = container_names.replace('local-ai-packaged-', '').replace('-1', '')

                    if service_name in self.services:
                        self.services[service_name].status = container.get('Status', 'Unknown')

        except Exception as e:
            print(f"Error updating service status: {e}")

    def check_port_conflicts(self) -> Dict[int, List[str]]:
        """Check for port binding conflicts across all services"""
        conflicts: Dict[int, List[str]] = {}
        port_to_services: Dict[int, List[str]] = {}

        for service_name, service in self.services.items():
            if service.port not in port_to_services:
                port_to_services[service.port] = []
            port_to_services[service.port].append(service_name)

        conflicts = {port: services for port, services in port_to_services.items() if len(services) > 1}
        return conflicts

    def find_available_port(self, start_port: int = 8000) -> int:
        """Find next available port"""
        port = start_port
        while port < 65535:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                try:
                    sock.bind(('', port))
                    return port
                except OSError:
                    port += 1
        return port

    def resolve_port_conflicts(self) -> Dict[str, Dict[int, int]]:
        """Resolve port conflicts by mapping services to available ports"""
        conflicts = self.check_port_conflicts()
        if not conflicts:
            return {}

        port_mappings: Dict[str, Dict[int, int]] = {}

        for port, services in conflicts.items():
            print(f"Port conflict detected on port {port} for services: {services}")

            # Skip the first service, reassign others
            for service_name in services[1:]:
                new_port = self.find_available_port(port + 1)
                port_mappings[service_name] = {port: new_port}
                print(f"Mapped {service_name} from port {port} to {new_port}")

        return port_mappings

    def start_services(self, services: Optional[List[str]] = None) -> Dict[str, bool]:
        """Start specified services or all services"""
        target_services = services if services else list(self.services.keys())
        results: Dict[str, bool] = {}

        for service_name in target_services:
            try:
                print(f"Starting {service_name}...")
                subprocess.run(
                    ['docker', 'compose', 'up', '-d', service_name],
                    capture_output=True, check=True
                )
                results[service_name] = True
                print(f"✓ {service_name} started successfully")
            except subprocess.CalledProcessError as e:
                print(f"✗ Failed to start {service_name}: {e}")
                results[service_name] = False

        return results

    def stop_services(self, services: Optional[List[str]] = None) -> Dict[str, bool]:
        """Stop specified services or all services"""
        target_services = services if services else list(self.services.keys())
        results: Dict[str, bool] = {}

        for service_name in target_services:
            try:
                print(f"Stopping {service_name}...")
                subprocess.run(
                    ['docker', 'compose', 'stop', service_name],
                    capture_output=True, check=True
                )
                results[service_name] = True
                print(f"✓ {service_name} stopped successfully")
            except subprocess.CalledProcessError as e:
                print(f"✗ Failed to stop {service_name}: {e}")
                results[service_name] = False

        return results

    def get_service_logs(self, service_name: str, lines: int = 50) -> Optional[str]:
        """Get recent logs for a service"""
        try:
            result = subprocess.run(
                ['docker', 'logs', f"local-ai-packaged-{service_name}-1", '--tail', str(lines)],
                capture_output=True, text=True, check=True
            )
            return result.stdout
        except Exception as e:
            return f"Error getting logs: {e}"

    def get_health_status(self) -> Dict[str, Dict]:
        """Get comprehensive health status of all services"""
        status = {}
        self.update_service_status()

        for service_name, service in self.services.items():
            status[service_name] = {
                'status': service.status,
                'port': service.port,
                'healthy': service.is_healthy,
                'running': service.is_running
            }

        return status

    def generate_config_summary(self) -> Dict:
        """Generate configuration summary for monitoring dashboard"""
        return {
            'services': self.get_health_status(),
            'port_conflicts': self.check_port_conflicts(),
            'port_mappings': self.resolve_port_conflicts(),
            'timestamp': time.time()
        }

def main():
    print("=== Legislative AI Service Manager ===\n")

    manager = ServiceManager()

    print("Discovered Services:")
    for name, service in manager.services.items():
        print(f"  {name}: Port {service.port}")

    print(f"\nTotal services discovered: {len(manager.services)}\n")

    # Check for conflicts
    conflicts = manager.check_port_conflicts()
    if conflicts:
        print("Port Conflicts Found:")
        for port, services in conflicts.items():
            print(f"  Port {port}: {services}")
    else:
        print("No port conflicts detected.")

    # Get health status
    print("\nHealth Status:")
    health = manager.get_health_status()
    for name, status in health.items():
        health_icon = "✓" if status['healthy'] and status['running'] else "✗"
        print(f"  {health_icon} {name}: {status['status']} (Port {status['port']})")

if __name__ == "__main__":
    main()
