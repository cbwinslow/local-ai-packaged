#!/usr/bin/env python3.10
"""
Network Monitor Report Generator
Tracks network traffic, port usage, connections, and potential security issues.
"""

import os
import json
import subprocess
import psutil
import socket
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

class NetworkMonitor:
    def __init__(self):
        self.report = {
            'timestamp': datetime.now().isoformat(),
            'network_interfaces': {},
            'listening_ports': {},
            'established_connections': {},
            'docker_networks': {},
            'port_conflicts': {},
            'security_analysis': {},
            'performance_metrics': {}
        }

    def collect_network_interfaces(self) -> Dict[str, Any]:
        """Collect information about network interfaces."""
        interfaces = {}

        try:
            for name, addrs in psutil.net_if_addrs().items():
                interfaces[name] = []
                for addr in addrs:
                    interfaces[name].append({
                        'family': str(addr.family).split('.')[-1],
                        'address': addr.address,
                        'netmask': attr.ntmask,
                        'broadcast': attr.broadcast if hasattr(addr, 'broadcast') else None,
                        'ptp': attr.ptp if hasattr(addr, 'ptp') else None
                    })
        except Exception as e:
            self.report['security_analysis'].setdefault('alerts', []).append(f"Failed to collect network interfaces: {e}")

        return interfaces

    def collect_listening_ports(self) -> Dict[str, Any]:
        """Collect all listening ports and associated processes."""
        ports = {}

        try:
            for conn in psutil.net_connections(kind='inet'):
                if conn.status == 'LISTEN':
                    port = conn.laddr.port
                    process_name = 'Unknown'
                    try:
                        process_name = psutil.Process(conn.pid).name() if conn.pid else 'Unknown'
                    except psutil.NoSuchProcess:
                        process_name = 'Process terminated'

                    ports[port] = {
                        'address': conn.laddr.ip if conn.laddr else '0.0.0.0',
                        'process': process_name,
                        'pid': conn.pid,
                        'protocol': 'TCP'
                    }

            # Check for UDP listeners too
            result = subprocess.run(['netstat', '-uln'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n')[2:]:  # Skip header lines
                    parts = line.split()
                    if len(parts) >= 4:
                        try:
                            port = int(parts[3].split(':')[-1])
                            if port not in ports:
                                ports[port] = {
                                    'address': parts[3].split(':')[0],
                                    'process': 'UDP Service',
                                    'protocol': 'UDP'
                                }
                        except (ValueError, IndexError):
                            continue

        except Exception as e:
            self.report['security_analysis'].setdefault('alerts', []).append(f"Failed to collect listening ports: {e}")

        return ports

    def collect_established_connections(self) -> Dict[str, Any]:
        """Collect established network connections."""
        connections = {
            'active': [],
            'by_process': {},
            'by_remote_ip': {},
            'recent_connections': []
        }

        try:
            for conn in psutil.net_connections(kind='inet'):
                if conn.status == 'ESTABLISHED':
                    connection_info = {
                        'local': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                        'remote': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                        'process': psutil.Process(conn.pid).name() if conn.pid else 'Unknown',
                        'pid': conn.pid
                    }

                    connections['active'].append(connection_info)

                    # Group by process
                    process_name = connection_info['process']
                    if process_name not in connections['by_process']:
                        connections['by_process'][process_name] = []
                    connections['by_process'][process_name].append(connection_info)

                    # Group by remote IP
                    if connection_info['remote']:
                        remote_ip = conn.raddr.ip
                        if remote_ip not in connections['by_remote_ip']:
                            connections['by_remote_ip'][remote_ip] = []
                        connections['by_remote_ip'][remote_ip].append(connection_info)

        except Exception as e:
            self.report['security_analysis'].setdefault('alerts', []).append(f"Failed to collect connections: {e}")

        return connections

    def collect_docker_networks(self) -> Dict[str, Any]:
        """Collect Docker network information."""
        docker_networks = {}

        try:
            result = subprocess.run(['docker', 'network', 'ls', '--format', 'json'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                networks_output = result.stdout.strip()
                if networks_output:
                    for line in networks_output.split('\n'):
                        line = line.strip()
                        if line:
                            try:
                                network = json.loads(line)
                                network_id = network.get('ID', 'Unknown')
                                docker_networks[network['Name']] = {
                                    'id': network_id,
                                    'driver': network.get('Driver', 'Unknown'),
                                    'scope': network.get('Scope', 'Unknown')
                                }

                                # Get network details
                                if network_id:
                                    detail_result = subprocess.run(
                                        ['docker', 'network', 'inspect', network_id],
                                        capture_output=True, text=True, timeout=5
                                    )
                                    if detail_result.returncode == 0:
                                        try:
                                            network_details = json.loads(detail_result.stdout.strip())
                                            if isinstance(network_details, list) and network_details:
                                                details = network_details[0]
                                                docker_networks[network['Name']]['containers'] = len(details.get('Containers', {}))
                                                docker_networks[network['Name']]['subnets'] = [
                                                    ipam['Config'] for ipam in details.get('IPAM', {}).get('Config', [])
                                                ]
                                        except json.JSONDecodeError:
                                            pass

                            except json.JSONDecodeError:
                                continue

        except Exception as e:
            self.report['security_analysis'].setdefault('alerts', []).append(f"Failed to collect Docker networks: {e}")

        return docker_networks

    def analyze_port_conflicts(self) -> Dict[str, Any]:
        """Analyze potential port conflicts."""
        conflicts = {
            'docker_vs_host': [],
            'internal_conflicts': [],
            'security_risks': []
        }

        try:
            # Load Docker Compose configuration
            import yaml
            with open('docker-compose.yml', 'r') as f:
                compose_data = yaml.safe_load(f)

            declared_ports = []
            if 'services' in compose_data:
                for service_name, service_config in compose_data['services'].items():
                    if 'ports' in service_config:
                        for port_mapping in service_config['ports']:
                            if isinstance(port_mapping, str):
                                # Format like "8080:80"
                                parts = port_mapping.split(':')
                                if len(parts) == 2:
                                    try:
                                        host_port = int(parts[0])
                                        container_port = int(parts[1])
                                        declared_ports.append((host_port, service_name, container_port))
                                    except ValueError:
                                        continue

            # Check for duplicates
            seen_ports = {}
            for port, service, container_port in declared_ports:
                if port in seen_ports:
                    conflicts['internal_conflicts'].append({
                        'port': port,
                        'services': [seen_ports[port], service],
                        'recommendation': 'Resolve port conflict by remapping one service'
                    })
                else:
                    seen_ports[port] = service

            # Check against listening ports
            listening_ports = self.collect_listening_ports()
            for declared_port, service, container_port in declared_ports:
                if declared_port in listening_ports:
                    existing_process = listening_ports[declared_port]['process']
                    if existing_process != service and not existing_process.startswith('docker'):
                        conflicts['docker_vs_host'].append({
                            'port': declared_port,
                            'docker_service': service,
                            'existing_process': existing_process,
                            'recommendation': 'Change Docker port mapping'
                        })

            # Check for security risks (common vulnerable ports)
            risky_ports = [21, 23, 25, 53, 80, 443, 1433, 1521, 3306, 3389, 5432, 8080, 8443]
            for port in risky_ports:
                if port in listening_ports:
                    process = listening_ports[port]['process']
                    if process not in ['docker', 'nginx', 'apache', 'sshd']:  # Expected services
                        conflicts['security_risks'].append({
                            'port': port,
                            'process': process,
                            'risk': 'Unusual service on potentially insecure port'
                        })

        except Exception as e:
            self.report['security_analysis'].setdefault('alerts', []).append(f"Failed to analyze port conflicts: {e}")

        return conflicts

    def collect_performance_metrics(self) -> Dict[str, Any]:
        """Collect network performance metrics."""
        metrics = {
            'interface_stats': {},
            'packet_stats': {},
            'error_rates': {}
        }

        try:
            # Network interface statistics
            for name, stats in psutil.net_io_counters(pernic=True).items():
                metrics['interface_stats'][name] = {
                    'bytes_sent': stats.bytes_sent,
                    'bytes_recv': stats.bytes_recv,
                    'packets_sent': stats.packets_sent,
                    'packets_recv': stats.packets_recv,
                    'errin': stats.errin,
                    'errout': stats.errout,
                    'dropin': stats.dropin,
                    'dropout': stats.dropout
                }

                # Calculate error rates
                total_packets = stats.packets_sent + stats.packets_recv
                total_errors = stats.errin + stats.errout
                if total_packets > 0:
                    metrics['error_rates'][name] = {
                        'error_rate': round((total_errors / total_packets) * 100, 4),
                        'packet_drop_rate': round(((stats.dropin + stats.dropout) / total_packets) * 100, 4) if (stats.dropin + stats.dropout) > 0 else 0,
                        'severity': 'High' if (total_errors / total_packets) > 0.01 else 'Low'
                    }

        except Exception as e:
            self.report['security_analysis'].setdefault('alerts', []).append(f"Failed to collect performance metrics: {e}")

        return metrics

    def generate_report(self) -> Dict[str, Any]:
        """Generate the complete network report."""
        print("Collecting network information...")

        self.report['network_interfaces'] = self.collect_network_interfaces()
        print("✓ Network interfaces collected")

        self.report['listening_ports'] = self.collect_listening_ports()
        print("✓ Listening ports collected")

        self.report['established_connections'] = self.collect_established_connections()
        print("✓ Connection information collected")

        self.report['docker_networks'] = self.collect_docker_networks()
        print("✓ Docker networks collected")

        self.report['port_conflicts'] = self.analyze_port_conflicts()
        print("✓ Port conflict analysis completed")

        self.report['performance_metrics'] = self.collect_performance_metrics()
        print("✓ Performance metrics collected")

        return self.report

    def save_report(self, filename: Optional[str] = None) -> str:
        """Save the report to a file."""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"reports/generated/network-report-{timestamp}.json"

        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, 'w') as f:
            json.dump(self.report, f, indent=2)

        print(f"Network report saved to: {filename}")
        return filename

def main():
    """Main entry point."""
    monitor = NetworkMonitor()
    report = monitor.generate_report()

    # Save report
    json_file = monitor.save_report()

    # Generate summary
    summary = {
        'listening_ports': len(report['listening_ports']),
        'established_connections': len(report['established_connections']['active']),
        'docker_networks': len(report['docker_networks']),
        'port_conflicts': len(report['port_conflicts']['docker_vs_host']) +
                         len(report['port_conflicts']['internal_conflicts']),
        'security_risks': len(report['port_conflicts']['security_risks']),
        'total_alerts': len(report['security_analysis'].get('alerts', []))
    }

    summary_file = json_file.replace('.json', '.summary')
    with open(summary_file, 'w') as f:
        f.write(f"NETWORK MONITOR SUMMARY\n")
        f.write(f"Generated: {report['timestamp']}\n")
        f.write(f"Listening Ports: {summary['listening_ports']}\n")
        f.write(f"Active Connections: {summary['established_connections']}\n")
        f.write(f"Docker Networks: {summary['docker_networks']}\n")
        f.write(f"Port Conflicts: {summary['port_conflicts']}\n")
        f.write(f"Security Risks: {summary['security_risks']}\n")
        f.write(f"Total Alerts: {summary['total_alerts']}\n")

    print(f"Summary saved to: {summary_file}")
    print("\nNetwork Monitor Summary:")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
