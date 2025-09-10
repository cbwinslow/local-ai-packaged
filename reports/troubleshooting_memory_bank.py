#!/usr/bin/env python3.10
"""
Troubleshooting Memory Bank
Maintains a historical record of troubleshooting attempts, solutions, and patterns
to build institutional knowledge and accelerate future problem resolution.
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional

class TroubleshootingMemoryBank:
    def __init__(self, memory_file: str = "reports/troubleshooting_memory.json"):
        self.memory_file = memory_file
        self.memory = self._load_memory()

    def _load_memory(self) -> Dict[str, Any]:
        """Load existing troubleshooting memory."""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                print(f"Warning: Could not load memory file {self.memory_file}, starting fresh")
                return self._initialize_memory()

        return self._initialize_memory()

    def _initialize_memory(self) -> Dict[str, Any]:
        """Initialize new memory bank structure."""
        return {
            'created': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'version': '1.0',
            'incidents': {},
            'solutions': {},
            'patterns': {},
            'statistics': {
                'total_incidents': 0,
                'successful_resolutions': 0,
                ' avg_resolution_time_hours': 0,
                'most_common_categories': [],
                'resolution_success_rate': 0.0
            },
            'metadata': {
                'system_info': {},
                'environment': 'local-ai-packaged'
            }
        }

    def _save_memory(self) -> None:
        """Save memory bank to file."""
        self.memory['last_updated'] = datetime.now().isoformat()
        os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)

        with open(self.memory_file, 'w') as f:
            json.dump(self.memory, f, indent=2, default=str)

    def _generate_incident_hash(self, description: str, category: str) -> str:
        """Generate unique hash for incident based on description and category."""
        content = f"{description.lower()}{category.lower()}{datetime.now().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()

    def add_incident(self, description: str, category: str,
                    services_affected: List[str] = None,
                    severity: str = "Medium",
                    symptoms: List[str] = None,
                    environment_ctx: Dict[str, Any] = None) -> str:
        """Add a new incident to the memory bank."""

        incident_id = self._generate_incident_hash(description, category)

        incident = {
            'id': incident_id,
            'description': description,
            'category': category,
            'services_affected': services_affected or [],
            'severity': severity,
            'symptoms': symptoms or [],
            'reported_at': datetime.now().isoformat(),
            'status': 'Reported',
            'troubleshooting_attempts': [],
            'resolution': None,
            'resolution_time_hours': None,
            'environment_context': environment_ctx or {},
            'similar_incidents': []
        }

        self.memory['incidents'][incident_id] = incident
        self.memory['statistics']['total_incidents'] += 1
        self._save_memory()

        print(f"Incident added with ID: {incident_id}")
        return incident_id

    def add_troubleshooting_attempt(self, incident_id: str,
                                   description: str, actions_taken: List[str],
                                   expected_outcome: str, actual_outcome: str,
                                   success: bool, duration_minutes: int = 0,
                                   notes: str = "", tools_used: List[str] = None) -> bool:
        """Add a troubleshooting attempt to an incident."""

        if incident_id not in self.memory['incidents']:
            print(f"Error: Incident {incident_id} not found")
            return False

        incident = self.memory['incidents'][incident_id]

        attempt = {
            'timestamp': datetime.now().isoformat(),
            'description': description,
            'actions_taken': actions_taken,
            'expected_outcome': expected_outcome,
            'actual_outcome': actual_outcome,
            'success': success,
            'duration_minutes': duration_minutes,
            'notes': notes,
            'tools_used': tools_used or []
        }

        incident['troubleshooting_attempts'].append(attempt)

        # Update incident status based on success
        if success:
            incident['status'] = 'Resolved'
            incident['resolution'] = actual_outcome
            # Calculate resolution time
            if incident.get('troubleshooting_attempts'):
                reported_at = datetime.fromisoformat(incident['reported_at'])
                resolved_at = datetime.fromisoformat(attempt['timestamp'])
                incident['resolution_time_hours'] = (resolved_at - reported_at).total_seconds() / 3600
        else:
            incident['status'] = 'Escalated'

        self._save_memory()
        return True

    def resolve_incident(self, incident_id: str, resolution_summary: str,
                        final_solution: str, prevention_recommendations: List[str] = None) -> bool:
        """Mark incident as resolved and add final solution."""

        if incident_id not in self.memory['incidents']:
            print(f"Error: Incident {incident_id} not found")
            return False

        incident = self.memory['incidents'][incident_id]

        incident['status'] = 'Resolved'
        incident['resolution'] = resolution_summary

        # Extract successful patterns from attempts
        successful_attempts = [att for att in incident['troubleshooting_attempts'] if att['success']]
        if successful_attempts:
            resolution_hash = hashlib.md5(resolution_summary.encode()).hexdigest()
            self.memory['solutions'][resolution_hash] = {
                'pattern': final_solution,
                'category': incident['category'],
                'successful_actions': successful_attempts[0]['actions_taken'],
                'created_from_incident': incident_id
            }

        if prevention_recommendations:
            incident['prevention_recommendations'] = prevention_recommendations

        self._save_memory()
        self._update_statistics()
        return True

    def search_similar_incidents(self, description: str, category: str = None) -> List[Dict[str, Any]]:
        """Search for similar incidents based on description and category."""

        similar = []
        search_terms = description.lower().split()[:5]  # First 5 words

        for incident_id, incident in self.memory['incidents'].items():
            match_score = 0

            # Category match
            if category and incident['category'].lower() == category.lower():
                match_score += 50

            # Description similarity
            desc_words = incident['description'].lower().split()[:5]
            for term in search_terms:
                if any(term in desc_word or desc_word in term for desc_word in desc_words):
                    match_score += 20

            # Symptoms match
            for symptom in incident.get('symptoms', []):
                symptom_words = symptom.lower().split()
                for search_term in search_terms:
                    if search_term in symptom_words:
                        match_score += 10

            if match_score > 30:
                similar.append({
                    'id': incident_id,
                    'score': match_score,
                    'description': incident['description'],
                    'status': incident['status'],
                    'resolution': incident['resolution'],
                    'resolution_time': incident.get('resolution_time_hours')
                })

        return sorted(similar, key=lambda x: x['score'], reverse=True)[:5]

    def get_category_statistics(self, category: str = None) -> Dict[str, Any]:
        """Get statistics for a specific category or all categories."""

        if category:
            incidents = [inc for inc in self.memory['incidents'].values() if inc['category'] == category]
        else:
            incidents = list(self.memory['incidents'].values())

        if not incidents:
            return {'error': f'No incidents found for category: {category}'}

        total = len(incidents)
        resolved = len([inc for inc in incidents if inc['status'] == 'Resolved'])
        avg_resolution_time = sum([inc['resolution_time_hours'] for inc in incidents
                                  if inc['resolution_time_hours']] or [0]) / max(resolved, 1)

        return {
            'category': category or 'All',
            'total_incidents': total,
            'resolved_incidents': resolved,
            'resolution_rate': round(resolved / total * 100, 2) if total > 0 else 0,
            'average_resolution_time_hours': round(avg_resolution_time, 2),
            'most_common_symptoms': self._get_common_symptoms(incidents),
            'recent_incidents': [inc['id'] for inc in incidents[-3:]]
        }

    def _get_common_symptoms(self, incidents: List[Dict]) -> List[str]:
        """Extract most common symptoms from incidents."""

        symptom_count = {}
        for incident in incidents:
            for symptom in incident.get('symptoms', []):
                symptom_count[symptom] = symptom_count.get(symptom, 0) + 1

        return [symptom for symptom, count in sorted(symptom_count.items(), key=lambda x: x[1], reverse=True)[:5]]

    def _update_statistics(self) -> None:
        """Update global statistics."""

        incidents = list(self.memory['incidents'].values())
        resolved = [inc for inc in incidents if inc['status'] == 'Resolved']

        self.memory['statistics'].update({
            'total_incidents': len(incidents),
            'successful_resolutions': len(resolved),
            'resolution_success_rate': round(len(resolved) / len(incidents) * 100, 2) if incidents else 0,
            'avg_resolution_time_hours': round(sum([inc['resolution_time_hours'] for inc in resolved
                                                   if inc['resolution_time_hours']]) / max(len(resolved), 1), 2)
        })

        # Update most common categories
        category_count = {}
        for incident in incidents:
            category_count[incident['category']] = category_count.get(incident['category'], 0) + 1

        self.memory['statistics']['most_common_categories'] = [
            cat for cat, _ in sorted(category_count.items(), key=lambda x: x[1], reverse=True)[:3]
        ]

    def generate_learned_solutions(self) -> List[Dict[str, Any]]:
        """Generate a list of learned solutions from resolved incidents."""

        solutions = []
        for incident in self.memory['incidents'].values():
            if incident['status'] == 'Resolved' and incident['resolution']:
                solutions.append({
                    'id': incident['id'],
                    'category': incident['category'],
                    'problem': incident['description'],
                    'solution': incident['resolution'],
                    'services_affected': incident['services_affected'],
                    'resolution_time_hours': incident.get('resolution_time_hours', 0),
                    'prevention_tips': incident.get('prevention_recommendations', [])
                })

        return sorted(solutions, key=lambda x: x['resolution_time_hours'])

    def create_report(self) -> str:
        """Generate a comprehensive report of troubleshooting history."""

        stats = self.get_category_statistics()
        learned_solutions = self.generate_learned_solutions()

        report = f"""
TROUBLESHOOTING MEMORY BANK REPORT
Generated: {datetime.now().isoformat()}

=== OVERVIEW ===
Total Incidents: {self.memory['statistics']['total_incidents']}
Successful Resolutions: {self.memory['statistics']['successful_resolutions']}
Resolution Success Rate: {self.memory['statistics']['resolution_success_rate']}%
Average Resolution Time: {self.memory['statistics']['avg_resolution_time_hours']} hours
Most Common Categories: {', '.join(self.memory['statistics']['most_common_categories'])}

=== LEARNED SOLUTIONS ===
"""

        for i, solution in enumerate(learned_solutions[:10], 1):  # Top 10 quick fixes
            report += f"\n{i}. {solution['category']}: '{solution['problem'][:50]}...'\n"
            report += f"   Solution: {solution['solution'][:100]}...\n"
            report += f"   Resolution Time: {solution['resolution_time_hours']:.1f} hours\n"
            if solution['prevention_tips']:
                report += f"   Prevention: {solution['prevention_tips'][0]}\n"

        return report

def main():
    """Main entry point for testing and demonstration."""

    # Initialize memory bank
    memory_bank = TroubleshootingMemoryBank()

    # Example: Add sample incidents if memory is empty
    if not memory_bank.memory['incidents']:
        print("Initializing memory bank with sample incidents...")

        # Sample incident 1: Docker port conflict
        incident1 = memory_bank.add_incident(
            description="Cannot start n8n service due to port 5678 already in use",
            category="Docker",
            services_affected=["n8n"],
            severity="High",
            symptoms=[
                "Port already allocated error",
                "Service startup failure",
                "n8n container exits immediately"
            ],
            environment_ctx={"os": "Linux", "docker_version": "24.0"}
        )

        memory_bank.add_troubleshooting_attempt(
            incident_id=incident1,
            description="Check for existing n8n process",
            actions_taken=[
                "Ran 'docker ps' to check running containers",
                "Ran 'lsof -i :5678' to identify process using port",
                "Found existing n8n container still running"
            ],
            expected_outcome="Identify conflicting process",
            actual_outcome="Found old n8n container from previous session",
            success=True,
            duration_minutes=5,
            notes="Previous container wasn't properly stopped",
            tools_used=["docker", "lsof"]
        )

        memory_bank.resolve_incident(
            incident_id=incident1,
            resolution_summary="Stopped conflicting n8n container and restarted services",
            final_solution="Use 'docker compose down' before starting new session",
            prevention_recommendations=[
                "Always run 'docker compose down -v' before switching environments",
                "Implement cleanup scripts for existing containers"
            ]
        )

        # Sample incident 2: Ollama model download failure
        incident2 = memory_bank.add_incident(
            description="Ollama fails to download qwen2.5 model",
            category="AI Models",
            services_affected=["ollama"],
            severity="Medium",
            symptoms=[
                "Model download times out",
                "Ollama logs show connection errors",
                "qwen2.5:7b model not available after service start"
            ]
        )

        memory_bank.add_troubleshooting_attempt(
            incident_id=incident2,
            description="Check network connectivity and disk space",
            actions_taken=[
                "Verified internet connection",
                "Ran 'df -h' to check disk space (had only 2GB free)",
                "Checked Ollama logs for specific error messages"
            ],
            expected_outcome="Identify disk space or network issues",
            actual_outcome="Found disk space issue - only 1GB free, needed ~4GB",
            success=True,
            duration_minutes=10,
            tools_used=["df", "ping", "docker logs"]
        )

        memory_bank.resolve_incident(
            incident_id=incident2,
            resolution_summary="Cleaned up disk space and restarted Ollama service",
            final_solution="Ensure at least 5GB free space for model downloads",
            prevention_recommendations=[
                "Monitor disk usage regularly",
                "Set up automatic cleanup of old Docker images",
                "Use external model storage if running low on space"
            ]
        )

    # Generate and display report
    report = memory_bank.create_report()
    print(report)

    # Save report to file
    report_file = f"reports/generated/memory-bank-report-{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    os.makedirs(os.path.dirname(report_file), exist_ok=True)

    with open(report_file, 'w') as f:
        f.write(report)

    print(f"Memory bank report saved to: {report_file}")

    # Show search capability
    print("\n=== SEARCH EXAMPLE ===")
    similar = memory_bank.search_similar_incidents("port conflict n8n", "Docker")
    print(f"Found {len(similar)} similar incidents:")
    for inc in similar[:3]:
        print(f"- {inc['description'][:50]}... (Match: {inc['score']}%)")

if __name__ == "__main__":
    main()
