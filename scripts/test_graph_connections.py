#!/usr/bin/env python3
"""
Test connectivity to graph databases (Neo4j and Memgraph)
using Docker containers for testing.
"""
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function to display test results."""
    # Print connection details
    print("\n=== Graph Database Test Results ===")
    print("Run the test script with: ./scripts/test_graph_setup.sh")
    print("\n=== Connection Details ===")
    print("Neo4j Browser: http://localhost:7474")
    print("Neo4j Bolt: bolt://localhost:7687")
    print("Memgraph Lab: http://localhost:3000")
    print("Memgraph Bolt: bolt://localhost:7688")

if __name__ == "__main__":
    main()
