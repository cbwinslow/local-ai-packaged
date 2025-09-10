#!/usr/bin/env python3.10
"""
System Health Report Generator
Gathers comprehensive information about the local AI stack health,
assets, networking, and operational status.
"""

import os
import json
import yaml
import subprocess
import psutil
import socket
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

class SystemHealthMonitor:
    def __init__(self):
        self.report = {
            'timestamp': datetime.now().isoformat(),
            'system_info': {},
            'docker_status': {},
            'network_info': {},
            'service_health': {},
            'resource_usage': {},
            'assets': {},
            'alerts': []
        }

    def collect_system_info(self) -> Dict[str, Any]:
        """Collect basic system information."""
        try:
            uname = os.uname()
            return {
                'hostname': uname.nodename,
                'os': uname.sysname,
                'kernel': uname.release,
                'architecture': uname.machine,
                'cpus': psutil.cpu_count(logical=True),
                'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
                'disk_total_gb': round(psutil.disk_usage('/').total / (1024**3), 2)
            }
        except Exception as e:
            self.report['alerts'].append(f"Failed to collect system info: {e}")
            return {}

    def collect_docker_status(self) -> Dict[str, Any]:
        """Collect Docker containers and services status."""
        docker_info = {
            'containers': [],
            'images': [],
            'volumes': [],
            'networks': []
        }

        try:
            # Get running containers
            result = subprocess.run(
                ['docker', 'ps', '--format', 'json'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                containers_output = result.stdout.strip()
                if containers_output:
                    containers = []
                    for line in containers_output.split('\n'):
                        line = line.strip()
                        if line:
                            try:
                                container = json.loads(line)
                                containers.append({
                                    'name': container.get('Names', 'Unknown'),
                                    'image': container.get('Image', 'Unknown'),
                                    'status': container.get('Status', 'Unknown'),
                                    'ports': container.get('Ports', ''),
                                    'size': container.get('Size', '')
                                })
                            except json.JSONDecodeError:
                                continue
                    docker_info['containers'] = containers

            # Get images
            result = subprocess.run(
                ['docker', 'images', '--format', 'json'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                images_output = result.stdout.strip()
                if images_output:
                    images = []
                    for line in images_output.split('\n'):
                        line = line.strip()
                        if line:
                            try:
                                image = json.loads(line)
                                images.append({
                                    'repository': image.get('Repository', 'Unknown'),
                                    'tag': image.get('Tag', 'Unknown'),
                                    'size': image.get('Size', 'Unknown'),
                                    'created': image.get('CreatedAt', 'Unknown')
                                })
                            except json.JSONDecodeError:
                                continue
                    docker_info['images'] = images

        except subprocess.TimeoutExpired:
            self.report['alerts'].append("Docker status collection timed out")
        except Exception as e:
            self.report['alerts'].append(f"Failed to collect Docker status: {e}")

        return docker_info

    def collect_network_info(self) -> Dict[str, Any]:
        """Collect network information including ports and connections."""
        network_info = {
            'listening_ports': [],
            'port_conflicts': [],
            'network_connections': []
        }

        try:
            # Get listening ports
            for conn in psutil.net_connections(kind='inet'):
                if conn.status == 'LISTEN':
                    network_info['listening_ports'].append({
                        'port': conn.laddr.port,
                        'address': conn.laddr.ip if conn.laddr else '0.0.0.0',
                        'process': psutil.Process(conn.pid).name() if conn.pid else 'Unknown'
                    })

            # Check for port conflicts (same port in docker-compose.yml)
            try:
                with open('docker-compose.yml', 'r') as f:
                    compose_data = yaml.safe_load(f)

                declared_ports = []
                if 'services' in compose_data:
                    for service_name, service_config in compose_data['services'].items():
                        if 'ports' in service_config:
                            for port_mapping in service_config['ports']:
                                if isinstance(port_mapping, str):
                                    host_port = port_mapping.split(':')[0]
                                    declared_ports.append(int(host_port))

                # Check for duplicates
                seen_ports = set()
                for port in declared_ports:
                    if port in seen_ports:
                        network_info['port_conflicts'].append(port)
                    seen_ports.add(port)

            except Exception as e:
                self.report['alerts'].append(f"Failed to analyze port conflicts: {e}")

        except Exception as e:
            self.report['alerts'].append(f"Failed to collect network info: {e}")

        return network_info

    def collect_service_health(self) -> Dict[str, Any]:
        """Collect health status of key services."""
        services_to_check = {
            'ollama': {'port': 11434, 'endpoint': '/api/version'},
            'n8n': {'port': 5678, 'endpoint': '/healthz'},
            'supabase': {'port': 8005, 'endpoint': '/health'},
            'open-webui': {'port': 8080, 'endpoint': '/'},
            'qdrant': {'port': 6333, 'endpoint': '/health'},
            'neo4j': {'port': 7474, 'endpoint': '/'},
            'flowise': {'port': 3001, 'endpoint': '/'},
            'langfuse': {'port': 3000, 'endpoint': '/health'}
        }

        health_status = {}

        for service_name, config in services_to_check.items():
            status = {
                'reachable': False,
                'response_time_ms': None,
                'http_status': None,
                'error': None
            }

            try:
                import requests
                import socket

                # Check if port is open
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex(('localhost', config['port']))

                if result == 0:
                    status['reachable'] = True

                    # Try HTTP health check
                    try:
                        start_time = time.time()
                        response = requests.get(f'http://localhost:{config["port"]}{config["endpoint"]}', timeout=5)
                        status['response_time_ms'] = round((time.time() - start_time) * 1000, 2)
                        status['http_status'] = response.status_code
                    except requests.exceptions.RequestException as e:
                        status['error'] = str(e)

                sock.close()

            except Exception as e:
                status['error'] = str(e)
                self.report['alerts'].append(f"Health check for {service_name} failed: {e}")

            health_status[service_name] = status

        return health_status

    def collect_resource_usage(self) -> Dict[str, Any]:
        """Collect system resource usage."""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'memory_used_gb': round(psutil.virtual_memory().used / (1024**3), 2),
                'disk_usage_percent': psutil.disk_usage('/').percent,
                'disk_free_gb': round(psutil.disk_usage('/').free / (1024**3), 2),
                'network_connections': len(psutil.net_connections())
            }
        except Exception as e:
            self.report['alerts'].append(f"Failed to collect resource usage: {e}")
            return {}

    def collect_assets(self) -> Dict[str, Any]:
        """Collect information about project assets."""
        assets = {
            'files': {},
            'configs': {},
            'workflows': {},
            'volumes': {}
        }

        # Count files in key directories
        try:
            assets['files']['docs'] = len([f for f in os.listdir('docs') if f.endswith('.md')])
            assets['files']['reports'] = len(os.listdir('reports'))
            assets['workflows']['n8n'] = len([f for f in os.listdir('n8n/backup/workflows') if f.endswith('.json')])
            assets['workflows']['flowise'] = len([f for f in os.listdir('flowise') if f.endswith('.json')])

        except Exception as e:
            self.report['alerts'].append(f"Failed to collect file counts: {e}")

        # Check configuration files
        try:
            assets['configs']['docker_compose'] = False
            if os.path.exists('docker-compose.yml'):
                assets['configs']['docker_compose'] = True
                with open('docker-compose.yml', 'r') as f:
                    compose_data = yaml.safe_load(f)
                    assets['configs']['services'] = len(compose_data.get('services', {}))

            assets['configs']['env_file'] = os.path.exists('.env')
            assets['configs']['caddyfile'] = os.path.exists('Caddyfile')

        except Exception as e:
            self.report['alerts'].append(f"Failed to analyze configurations: {e}")

        return assets

    def generate_report(self) -> Dict[str, Any]:
        """Generate the complete health report."""
        print("Collecting system health information...")

        self.report['system_info'] = self.collect_system_info()
        print("✓ System info collected")

        self.report['docker_status'] = self.collect_docker_status()
        print("✓ Docker status collected")

        self.report['network_info'] = self.collect_network_info()
        print("✓ Network info collected")

        self.report['service_health'] = self.collect_service_health()
        print("✓ Service health collected")

        self.report['resource_usage'] = self.collect_resource_usage()
        print("✓ Resource usage collected")

        self.report['assets'] = self.collect_assets()
        print("✓ Assets inventory collected")

        return self.report

    def save_report(self, filename: Optional[str] = None) -> str:
        """Save the report to a file."""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"reports/generated/health-report-{timestamp}.json"

        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, 'w') as f:
            json.dump(self.report, f, indent=2)

        print(f"Health report saved to: {filename}")
        return filename

    def generate_text_report(self) -> str:
        """Generate a human-readable text report."""
        report = self.report

        text_report = f"""
SYSTEM HEALTH REPORT
Generated: {report['timestamp']}

=== SYSTEM INFO ===
Hostname: {report['system_info'].get('hostname', 'Unknown')}
OS: {report['system_info'].get('os', 'Unknown')} {report['system_info'].get('kernel', 'Unknown')}
Architecture: {report['system_info'].get('architecture', 'Unknown')}
CPUs: {report['system_info'].get('cpus', 'Unknown')}
Memory: {report['system_info'].get('memory_total_gb', 'Unknown')} GB total
Disk: {report['system_info'].get('disk_total_gb', 'Unknown')} GB total

=== RESOURCE USAGE ===
CPU Usage: {report['resource_usage'].get('cpu_percent', 'Unknown')}%
Memory Usage: {report['resource_usage'].get('memory_percent', 'Unknown')}% ({report['resource_usage'].get('memory_used_gb', 'Unknown')} GB used)
Disk Usage: {report['resource_usage'].get('disk_usage_percent', 'Unknown')}%
Network Connections: {report['resource_usage'].get('network_connections', 'Unknown')}

=== DOCKER STATUS ===
Running Containers: {len(report['docker_status'].get('containers', []))}
Docker Images: {len(report['docker_status'].get('images', []))}

=== SERVICE HEALTH ===
"""

        for service, health in report['service_health'].items():
            reachable = "✓" if health.get('reachable') else "✗"
            response_time = health.get('response_time_ms')
            status = health.get('http_status')
            error = health.get('error')

            text_report += f"{reachable} {service}: "
            if reachable:
                text_report += f"Healthy"
                if response_time:
                    text_report += f" ({response_time}ms)"
                if status:
                    text_report += f" [HTTP {status}]"
            else:
                text_report += f"Unhealthy"
                if error:
                    text_report += f" ({error[:50]}...)"

            text_report += "\n"

        text_report += f"""
=== ASSETS ===
Documentation Files: {report['assets'].get('files', {}).get('docs', 'Unknown')}
Report Files: {report['assets'].get('files', {}).get('reports', 'Unknown')}
n8n Workflows: {report['assets'].get('workflows', {}).get('n8n', 'Unknown')}
Flowise Workflows: {report['assets'].get('workflows', {}).get('flowise', 'Unknown')}
Docker Services: {report['assets'].get('configs', {}).get('services', 'Unknown')}

=== ALERTS ===
"""
        if report['alerts']:
            for alert in report['alerts']:
                text_report += f"⚠ {alert}\n"
        else:
            text_report += "No alerts\n"

        return text_report

def main():
    """Main entry point."""
    monitor = SystemHealthMonitor()
    monitor.generate_report()

    # Save JSON report
    json_file = monitor.save_report()

    # Save text report
    text_report = monitor.generate_text_report()
    text_file = json_file.replace('.json', '.txt')
    with open(text_file, 'w') as f:
        f.write(text_report)

    print(f"Text report saved to: {text_file}")
    print("\n" + "="*60)
    print(text_report)

if __name__ == "__main__":
    main()
