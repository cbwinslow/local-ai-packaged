#!/usr/bin/env python3
"""
AI Tools Integration Script - Simplified version
"""

import os
import subprocess
from pathlib import Path

class AIToolsManager:
    def __init__(self):
        self.root_dir = Path(__file__).parent.absolute()
    
    def setup_tool(self, tool_name: str):
        """Set up a specific tool with required directories."""
        tool_dirs = {
            'graphite': ['graphite/data', 'graphite/logs'],
            'libsql': ['libsql_data'],
            'neo4j': ['neo4j/data', 'neo4j/logs'],
            'crewai': ['crewai/agents', 'crewai/tasks'],
            'letta': ['letta_data'],
            'falkor': ['falkor_data'],
            'graphrag': ['graphrag_data'],
            'llama': ['llama_data'],
            'crawl4ai': ['crawl4ai_data']
        }
        
        if tool_name == 'all':
            for tool in tool_dirs:
                self.setup_tool(tool)
            return
            
        if tool_name not in tool_dirs:
            print(f"Unknown tool: {tool_name}")
            return
            
        print(f"Setting up {tool_name}...")
        for directory in tool_dirs[tool_name]:
            (self.root_dir / directory).mkdir(parents=True, exist_ok=True)
        print(f"{tool_name.capitalize()} setup complete.")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Manage AI tools')
    parser.add_argument('tool', nargs='?', default='all',
                      help='Tool to set up (default: all)')
    
    args = parser.parse_args()
    manager = AIToolsManager()
    manager.setup_tool(args.tool.lower())

if __name__ == "__main__":
    main()
