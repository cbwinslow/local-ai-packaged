#!/usr/bin/env python3.10
import yaml
import sys

def validate_yaml(file_path):
    try:
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
        print(f"YAML validation for {file_path}: Valid")
        return True
    except yaml.YAMLError as e:
        print(f"YAML validation for {file_path}: Invalid - {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "docker-compose.yml"
    validate_yaml(file_path)