#!/usr/bin/env python3
"""
Port Manager - Dynamic port assignment and conflict resolution
Manages service ports and automatically resolves conflicts
"""

import subprocess
import socket
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class PortManager:
    def __init__(self, compose_file: str = "docker-compose.yml"):
        self.compose_file = compose_file
        self.used_ports: List[int] = []
        self.service_ports: Dict[str, Tuple[int, int]] = {}  # current: new

    def load_compose_ports(self) -> Dict[str, str]:
        """Load current port configurations from docker-compose.yml"""
        try:
            import yaml
            with open(self.compose_file, 'r') as f:
                compose_data = yaml.safe_load(f)
        except Exception as e:
            print(f"Warning: Could not load {self.compose_file}: {e}")
            return {}

        port_mappings = {}
        if 'services' in compose_data:
            for service_name, config in compose_data['services'].items():
                if 'ports' in config and config['ports']:
                    port_list = config['ports']
                    # Handle different port formats
                    for port_config in port_list:
                        if isinstance(port_config, dict):
                            port_info = port_config.get('published', 'Unknown')
                        elif isinstance(port_config, str):
                            if ':' in port_config:
                                port_info = port_config.split(':')[0]
                            else:
                                port_info = port_config
                        else:
                            port_info = str(port_config)

                        port_mappings[service_name] = port_info
                        break  # Take first port only

        return port_mappings

    def check_used_ports(self) -> List[int]:
        """Check which ports are currently in use by processes"""
        used_ports = []

        # Use lsof for exact port checking
        try:
            result = subprocess.run(
                ['lsof', '-i', ':0-65535'],
                capture_output=True, text=True,
                timeout=10  # Add timeout to prevent hanging
            )
            for line in result.stdout.split('\n'):
                if 'LISTEN' in line:
                    parts = line.split()
                    if len(parts) >= 9:
                        address = parts[8]
                        # Extract port from address like 127.0.0.1:8080
                        if ':' in address and address.split(':')[1].isdigit():
                            port = int(address.split(':')[1])
                            if port not in used_ports:
                                used_ports.append(port)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Fallback to netstat if lsof fails
            try:
                result = subprocess.run(
                    ['netstat', '-tln'],
                    capture_output=True, text=True,
                    timeout=5
                )
                for line in result.stdout.split('\n'):
                    if 'LISTEN' in line:
                        parts = line.split()
                        if len(parts) >= 4:
                            address = parts[3]
                            port_str = address.split(':')[-1].strip() if ':' in address else address
                            if port_str.isdigit():
                                port = int(port_str)
                                if port not in used_ports:
                                    used_ports.append(port)
            except (subprocess.TimeoutExpired, FileNotFoundError):
                print("Warning: Could not determine used ports")

        return sorted(set(used_ports))

    def is_port_available(self, port: int) -> bool:
        """Check if a specific port is available"""
        try:
            # Check if we can bind to the port
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(('127.0.0.1', port))
                return result != 0  # 0 means port is in use
        except Exception:
            return False

    def find_next_available_port(self, start_port: int = 8000, count: int = 1) -> List[int]:
        """Find the next available port(s) starting from start_port"""
        available_ports = []
        current_port = start_port

        while len(available_ports) < count and current_port < 65535:
            if self.is_port_available(current_port):
                available_ports.append(current_port)
            current_port += 1

        if len(available_ports) < count:
            print(f"Warning: Could not find {count} available ports starting from {start_port}")

        return available_ports

    def resolve_conflicts(self, save_changes: bool = True) -> Dict[str, Tuple[int, int]]:
        """Resolve port conflicts by finding alternative ports"""
        print("=== Port Conflict Resolution ===")

        current_ports = self.load_compose_ports()
        self.used_ports = self.check_used_ports()

        print(f"Currently used system ports: {[p for p in self.used_ports if p < 9000][:10]}...")

        port_mappings = {}
        port_conflicts = {}

        # Check conflicts
        for service_name, port_str in current_ports.items():
            if not port_str or not port_str.isdigit():
                continue

            port = int(port_str)

            # Check if port is in conflict
            if port in self.used_ports:
                print(f"❌ Port conflict: {service_name} port {port} is already in use")
                port_conflicts[service_name] = port
            else:
                print(f"✅ {service_name}: Port {port} is available")

        # Resolve conflicts
        for service_name, current_port in port_conflicts.items():
            new_ports = self.find_next_available_port(current_port + 1, 1)
            if new_ports:
                new_port = new_ports[0]
                port_mappings[service_name] = (current_port, new_port)
                print(f"🔄 Mapped {service_name}: Port {current_port} → {new_port}")
            else:
                print(f"❌ Could not find alternative port for {service_name}")

        if not port_mappings:
            print("\n✅ No port conflicts found or all resolved successfully")
        else:
            print(f"\n🔄 Port mappings to resolve conflicts: {len(port_mappings)}")

        # Save changes if requested
        if save_changes and port_mappings:
            self.save_port_mappings(port_mappings)

        return port_mappings

    def save_port_mappings(self, port_mappings: Dict[str, Tuple[int, int]]):
        """Save port mappings to docker-compose.override.yml"""
        override_file = "docker-compose.override.ports.yml"
        override_config = {"services": {}}

        # Read existing overrides
        if Path(override_file).exists():
            with open(override_file, 'r') as f:
                override_config = yaml.safe_load(f) or {"services": {}}

        if 'services' not in override_config:
            override_config['services'] = {}

        # Apply port mappings
        for service_name, (old_port, new_port) in port_mappings.items():
            service_key = service_name.replace('\\','-')  # Handle service names with slashes

            if service_key not in override_config['services']:
                override_config['services'][service_key] = {}

            # Build port mapping string
            override_config['services'][service_key]['ports'] = [f"{new_port}:8080"]  # Assuming internal port 8080

        # Save override file
        with open(override_file, 'w') as f:
            yaml.dump(override_config, f, default_flow_style=False)

        print(f"💾 Saved port mappings to {override_file}")

        # Update compose file
        print("\n📝 To apply changes, restart services:")
        print("   docker compose down")
        print("   docker compose up -d")

    def get_port_status(self) -> Dict[str, bool]:
        """Get status of all configured ports"""
        current_ports = self.load_compose_ports()
        self.used_ports = self.check_used_ports()

        status = {}
        for service_name, port_str in current_ports.items():
            if port_str and port_str.isdigit():
                port = int(port_str)
                status[service_name] = port not in self.used_ports
            else:
                status[service_name] = False  # Invalid port

        return status

def main():
    print("=== Port Conflict Resolution Manager ===\n")

    manager = PortManager()

    # Show current status
    print("Current Port Configuration:")
    for service, port_str in manager.load_compose_ports().items():
        print(f"  {service}: {port_str}")

    print("\nChecking for conflicts...")
    port_mappings = manager.resolve_conflicts()

    if port_mappings:
        print("\nPort Mappings Created:")
        for service, (old_port, new_port) in port_mappings.items():
            print(f"  {service}: {old_port} → {new_port}")
    else:
        print("\nNo conflicts found - all ports appear available!")

    # Show summary stats
    print("\n=== Summary ===")
    status = manager.get_port_status()
    available = sum(status.values())
    total = len(status)
    print(f"Services with available ports: {available}/{total}")

    if available < total:
        print("\n⚠️  Some ports are in conflict. Run the script with --resolve to fix automatically.")
        print("   python3 port-manager.py --resolve")
        sys.exit(1)
    else:
        print("\n✅ All service ports are available!")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--resolve':
        manager = PortManager()
        manager.resolve_conflicts(save_changes=True)
        print("Port conflicts resolved! Restart services to apply changes.")
    else:
        main()
