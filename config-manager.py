#!/usr/bin/env python3
"""
Configuration Management System
Evaluates and manages configuration storage options (Supabase DB vs Config Files)
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import sqlite3
import subprocess
import requests

class ConfigEvaluator:
    """Evaluates best configuration storage option"""

    def __init__(self):
        self.criteria = {
            'performance': 0,
            'reliability': 0,
            'complexity': 0,
            'scalability': 0,
            'development_speed': 0,
            'maintenance_cost': 0,
            'monitoring_overhead': 0,
            'backup_complexity': 0
        }

    def evaluate_supabase_db(self) -> Dict[str, Any]:
        """Evaluate using Supabase database for configuration"""
        pros = [
            "Centralized configuration management",
            "High availability and replication",
            "Real-time configuration updates",
            "Built-in authentication and permissions",
            "Easy to query and filter configurations",
            "Version control through migrations",
            "Consistent with project database approach"
        ]

        cons = [
            "Requires database service to be running",
            "Additional network calls for config retrieval",
            "Database complexity for simple key-value storage",
            "Migration requirements for schema changes",
            "Dependent on PostgreSQL performance",
            "More complex backup/restore procedures",
            "Application startup delay waiting for DB"
        ]

        scores = {
            'performance': 7,    # Good but involves network calls
            'reliability': 9,    # High availability with replication
            'complexity': 6,     # Moderately complex
            'scalability': 9,    # Scales well with PostgreSQL
            'development_speed': 7,  # Quick to implement
            'maintenance_cost': 8,    # Lower maintenance with managed service
            'monitoring_overhead': 8,  # Built-in monitoring
            'backup_complexity': 7     # Standard database backups
        }

        return {
            'method': 'Supabase Database',
            'pros': pros,
            'cons': cons,
            'scores': scores,
            'total_score': sum(scores.values()),
            'feasibility': self.check_supabase_feasibility()
        }

    def evaluate_config_files(self) -> Dict[str, Any]:
        """Evaluate using YAML/JSON configuration files"""
        pros = [
            "Fast startup - no database dependencies",
            "Simple file-based approach",
            "Easy to version control with git",
            "Immutable configurations for consistency",
            "Simple backup/restore procedures",
            "No additional network overhead",
            "Easy to edit manually for debugging",
            "Works offline for development"
        ]

        cons = [
            "File system permissions and access control",
            "No real-time updates without file watchers",
            "Manual synchronization across instances",
            "Limited query capabilities",
            "Version control conflicts possible",
            "Limited concurrent access controls",
            "Manual configuration validation",
            "Single point of failure for file system"
        ]

        scores = {
            'performance': 10,   # Fastest possible
            'reliability': 7,    # Depends on file system reliability
            'complexity': 8,     # Simple to implement
            'scalability': 6,    # Limited scaling capabilities
            'development_speed': 10,  # Very quick to implement
            'maintenance_cost': 7,     # Low maintenance
            'monitoring_overhead': 6,   # Basic file system monitoring
            'backup_complexity': 9      # Simple file backups
        }

        return {
            'method': 'Configuration Files',
            'pros': pros,
            'cons': cons,
            'scores': scores,
            'total_score': sum(scores.values()),
            'feasibility': self.check_filesystem_feasibility()
        }

    def check_supabase_feasibility(self) -> Dict[str, Any]:
        """Check if Supabase database option is feasible"""
        feasibility = {
            'supabase_running': False,
            'database_schema': False,
            'network_access': False,
            'migrations_ready': False
        }

        try:
            # Check if Supabase database is accessible
            api_url = os.getenv('SUPABASE_URL', 'http://localhost:8000')
            anon_key = os.getenv('ANON_KEY', '')
            if anon_key:
                response = requests.get(f"{api_url}/rest/v1/health-check", headers={'apikey': anon_key}, timeout=5)
                feasibility['supabase_running'] = response.status_code == 200
                feasibility['network_access'] = True
        except:
            feasibility['supabase_running'] = False
            feasibility['network_access'] = False

        # Check for existing schema/migrations
        # This would typically check for existing tables or migration files
        feasibility['database_schema'] = False  # Implement database check
        feasibility['migrations_ready'] = False  # Implement migration check

        return feasibility

    def check_filesystem_feasibility(self) -> Dict[str, Any]:
        """Check if file system configuration is feasible"""
        feasibility = {
            'config_directory': False,
            'permissions': False,
            'git_enabled': False,
            'backup_path': False
        }

        # Check config directory exists and is accessible
        config_dir = Path('./config')
        if config_dir.exists():
            try:
                # Test write permissions
                test_file = config_dir / '.test'
                test_file.write_text('test')
                test_file.unlink()
                feasibility['config_directory'] = True
                feasibility['permissions'] = True
            except:
                feasibility['permissions'] = False

        # Check if git is enabled for version control
        feasibility['git_enabled'] = (Path('.git').exists())

        # Check backup directory
        backup_dir = Path('./config/backups')
        feasibility['backup_path'] = backup_dir.mkdir(exist_ok=True) or backup_dir.exists()

        return feasibility

    def recommend_best_option(self) -> Dict[str, Any]:
        """Recommend the best configuration storage option"""
        supabase_eval = self.evaluate_supabase_db()
        files_eval = self.evaluate_config_files()

        print("=== Configuration Storage Evaluation ===\n")

        print("Option 1: Supabase Database")
        print(f"Total Score: {supabase_eval['total_score']}/80 ({supabase_eval['total_score']/80*100:.1f}%)")
        print("Pros:")
        for pro in supabase_eval['pros']:
            print(f"  ✓ {pro}")
        print("Cons:")
        for con in supabase_eval['cons']:
            print(f"  ✗ {con}")

        print("\nOption 2: Configuration Files")
        print(f"Total Score: {files_eval['total_score']}/80 ({files_eval['total_score']/80*100:.1f}%)")
        print("Pros:")
        for pro in files_eval['pros']:
            print(f"  ✓ {pro}")
        print("Cons:")
        for con in files_eval['cons']:
            print(f"  ✗ {con}")

        # Determine recommendation
        if (supabase_eval['total_score'] > files_eval['total_score'] and
            all(supabase_eval['feasibility'].values())):
            recommendation = {
                'chosen': 'Supabase Database',
                'reason': 'Higher score with fully functional environment',
                'implementation_notes': [
                    'Create configuration tables in existing Supabase schema',
                    'Implement caching layer for performance',
                    'Add configuration validation middleware',
                    'Set up configuration audit trails'
                ]
            }
        else:
            recommendation = {
                'chosen': 'Configuration Files',
                'reason': 'Simpler, faster, and more reliable for current environment',
                'implementation_notes': [
                    'Use YAML files with structured directories',
                    'Implement hot-reload for configuration changes',
                    'Add configuration validation and type checking',
                    'Set up automatic backups to git'
                ]
            }

        print(f"\n🎯 RECOMMENDATION: {recommendation['chosen']}")
        print(f"Reason: {recommendation['reason']}")
        print("\n📋 Implementation Notes:")
        for note in recommendation['implementation_notes']:
            print(f"  • {note}")

        return recommendation

class ConfigManager:
    """Configuration management with chosen persistence method"""

    def __init__(self, method: str = 'files'):
        self.method = method
        self.config_dir = Path('./config')
        self.config_file = self.config_dir / 'services.json'

    def initialize_config(self):
        """Initialize configuration structure"""
        self.config_dir.mkdir(exist_ok=True)
        (self.config_dir / 'backups').mkdir(exist_ok=True)

        if not self.config_file.exists():
            default_config = {
                'services': {},
                'global_settings': {
                    'auto_restart': True,
                    'log_level': 'info',
                    'health_check_interval': 30
                },
                'version': '1.0.0',
                'last_updated': None
            }
            self.save_config(default_config)

    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except:
            return {}

    def save_config(self, config: Dict[str, Any]):
        """Save configuration to file"""
        # Create backup
        if self.config_file.exists():
            backup_file = self.config_dir / 'backups' / f'config.backup.{int(__import__("time").time())}'
            self.config_file.replace(backup_file)

        config['last_updated'] = __import__("time").time()
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)

    def update_service_config(self, service_name: str, config: Dict[str, Any]):
        """Update specific service configuration"""
        current_config = self.get_config()
        if 'services' not in current_config:
            current_config['services'] = {}

        current_config['services'][service_name] = {
            **current_config['services'].get(service_name, {}),
            **config
        }
        self.save_config(current_config)

def main():
    evaluator = ConfigEvaluator()
    recommendation = evaluator.recommend_best_option()

    print("\n" + "="*50)
    print("CONFIGURATION MANAGEMENT IMPLEMENTATION")
    print("="*50)

    if recommendation['chosen'] == 'Configuration Files':
        print("🚀 Implementing File-Based Configuration System...")
        config_manager = ConfigManager(method='files')
        config_manager.initialize_config()

        # Example service configurations
        services_config = {
            'supabase-db': {
                'type': 'database',
                'port': 5432,
                'health_check': '/health',
                'retry_count': 3,
                'timeout': 30
            },
            'n8n': {
                'type': 'workflow',
                'port': 5678,
                'dependencies': ['postgres'],
                'auto_restart': True
            },
            'neo4j': {
                'type': 'graph-database',
                'ports': {
                    'http': 7474,
                    'bolt': 7687
                },
                'health_check': '/db/neo4j/availability'
            }
        }

        for service_name, config in services_config.items():
            config_manager.update_service_config(service_name, config)

        print("✅ Configured services:")
        for service in services_config.keys():
            print(f"  - {service}")

        print("\n💾 Configuration saved to: ./config/services.json")
        print("📁 Backup directory: ./config/backups/")

        print("\n🔧 Next Steps:")
        print("1. Edit .env file to enable file-based configuration")
        print("2. Implement hot-reload for configuration changes")
        print("3. Add configuration validation in service startup scripts")

    elif recommendation['chosen'] == 'Supabase Database':
        print("🚀 Implementing Database-Based Configuration System...")
        print("TODO: Implement Supabase configuration tables and queries")
        print("1. Create configuration schema in Supabase")
        print("2. Implement configuration API endpoints")
        print("3. Add caching layer for performance")

if __name__ == "__main__":
    main()
