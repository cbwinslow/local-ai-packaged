#!/usr/bin/env python3
"""
Fetch Secrets from Bitwarden

This script helps fetch API keys and other secrets from Bitwarden and update the .env file.
"""

import os
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional, List

# Configuration
ENV_FILE = ".env"
BW_CLI = "bw"

# Map of environment variables to Bitwarden item names
# Update these with your actual Bitwarden item names
SECRET_MAPPING = {
    "OPENAI_API_KEY": "OpenAI API Key",
    "SERPAPI_API_KEY": "SerpAPI Key",
    "LETTA_API_KEY": "Letta API Key",
    "GRAPHRAG_API_KEY": "GraphRAG API Key",
    "CRAWL4AI_API_KEY": "Crawl4AI API Key",
    "N8N_ENCRYPTION_KEY": "n8n Encryption Key",
    "N8N_USER_MANAGEMENT_JWT_SECRET": "n8n JWT Secret",
    "JWT_SECRET": "JWT Secret",
    "ANON_KEY": "Supabase Anon Key",
    "SERVICE_ROLE_KEY": "Supabase Service Role Key",
    "DASHBOARD_PASSWORD": "Dashboard Password"
}

class BitwardenManager:
    def __init__(self):
        self.bw_path = self._find_bw()
        self.session = None
    
    def _find_bw(self) -> str:
        """Find the Bitwarden CLI executable."""
        try:
            result = subprocess.run(
                ["which", "bw"], 
                capture_output=True, 
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            print(f"Error finding Bitwarden CLI: {e}")
        return "bw"  # Fallback to just 'bw' if not found in path
    
    def login(self) -> bool:
        """Log in to Bitwarden."""
        try:
            # Check if already logged in
            status = self._run_bw_command("status")
            if status.get("status") == "unlocked":
                print("Already logged in to Bitwarden")
                return True
            
            # Start interactive login
            print("Logging in to Bitwarden...")
            print("Please check your email for the verification code.")
            
            # Start the login process
            login_cmd = [self.bw_path, "login", "--raw"]
            print(f"Running: {' '.join(login_cmd)}")
            
            # Run the login command and capture the session key
            result = subprocess.run(
                login_cmd,
                input="",  # Start interactive login
                text=True,
                capture_output=True
            )
            
            if result.returncode == 0:
                self.session = result.stdout.strip()
                print("Successfully logged in to Bitwarden")
                return True
            else:
                print(f"Error logging in: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Error during Bitwarden login: {e}")
            return False
    
    def unlock(self) -> bool:
        """Unlock the Bitwarden vault."""
        try:
            # Check if already unlocked
            status = self._run_bw_command("status")
            if status.get("status") == "unlocked":
                print("Vault already unlocked")
                return True
            
            # Prompt for master password
            from getpass import getpass
            password = getpass("Enter your Bitwarden master password: ")
            
            # Unlock the vault
            result = subprocess.run(
                [self.bw_path, "unlock", "--raw", password],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.session = result.stdout.strip()
                print("Vault unlocked successfully")
                return True
            else:
                print(f"Error unlocking vault: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Error unlocking Bitwarden vault: {e}")
            return False
    
    def _run_bw_command(self, command: str, args: List[str] = None, session: bool = True) -> dict:
        """Run a Bitwarden CLI command and return the JSON output."""
        if args is None:
            args = []
            
        cmd = [self.bw_path, command] + args
        if session and self.session:
            cmd.extend(["--session", self.session])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"Error running command: {result.stderr}")
                return {}
                
            if not result.stdout.strip():
                return {}
                
            return json.loads(result.stdout)
            
        except json.JSONDecodeError:
            print(f"Failed to parse JSON output from Bitwarden")
            return {}
        except Exception as e:
            print(f"Error running Bitwarden command: {e}")
            return {}
    
    def get_secrets(self, item_names: List[str]) -> Dict[str, str]:
        """Get secrets from Bitwarden."""
        secrets = {}
        
        # First, sync to make sure we have the latest data
        print("Syncing with Bitwarden...")
        self._run_bw_command("sync")
        
        # Get all items
        print("Searching for items in Bitwarden...")
        items = self._run_bw_command("list", ["items"])
        
        if not isinstance(items, list):
            print("Failed to retrieve items from Bitwarden")
            return {}
        
        # Create a mapping of item names to items for easier lookup
        item_map = {item.get('name', '').lower(): item for item in items}
        
        # Find and retrieve each requested secret
        for env_var in item_names:
            item_name = SECRET_MAPPING.get(env_var, env_var)
            print(f"Looking for: {item_name}")
            
            # Try exact match first
            item = None
            for candidate_item in items:
                if candidate_item.get('name') == item_name:
                    item = candidate_item
                    break
            
            # If not found, try case-insensitive match
            if not item:
                item = item_map.get(item_name.lower())
            
            if not item:
                print(f"  ❌ Item not found: {item_name}")
                continue
            
            # Get the item details
            item_id = item.get('id')
            if not item_id:
                print(f"  ❌ No ID found for item: {item_name}")
                continue
            
            item_details = self._run_bw_command("get", ["item", item_id])
            if not item_details:
                print(f"  ❌ Failed to get details for item: {item_name}")
                continue
            
            # Extract the secret (assuming it's in the 'notes' field or a custom field)
            secret = None
            
            # Check notes field
            if item_details.get('notes'):
                secret = item_details['notes']
            
            # Check fields (for API keys, etc.)
            if not secret and 'fields' in item_details:
                for field in item_details['fields']:
                    if field.get('name', '').lower() in ['api key', 'key', 'secret', 'password']:
                        secret = field.get('value')
                        if secret:
                            break
            
            # Check login information
            if not secret and 'login' in item_details:
                login = item_details['login']
                secret = login.get('password') or login.get('totp')
            
            if secret:
                secrets[env_var] = secret
                print(f"  ✅ Found: {env_var}")
            else:
                print(f"  ⚠️  Found item but no secret: {item_name}")
        
        return secrets

class EnvManager:
    @staticmethod
    def load_env() -> dict:
        """Load environment variables from .env file."""
        env_vars = {}
        if os.path.exists(ENV_FILE):
            with open(ENV_FILE, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key] = value.strip('"\'')
        return env_vars
    
    @staticmethod
    def update_env(updates: dict):
        """Update .env file with new values."""
        # Read existing variables
        env_vars = EnvManager.load_env()
        
        # Update with new values
        env_vars.update(updates)
        
        # Write back to file
        with open(ENV_FILE, 'w') as f:
            for key, value in env_vars.items():
                f.write(f'{key}="{value}"\n')
        
        print(f"Updated {ENV_FILE} with {len(updates)} secrets")

def main():
    print("=== Bitwarden Secrets Fetcher ===\n")
    
    # Initialize managers
    bw = BitwardenManager()
    env_manager = EnvManager()
    
    # Check if Bitwarden is installed
    if not os.path.exists(bw.bw_path):
        print("Error: Bitwarden CLI (bw) is not installed.")
        print("Please install it from: https://bitwarden.com/help/cli/")
        sys.exit(1)
    
    # Login to Bitwarden
    if not bw.login():
        print("Failed to log in to Bitwarden")
        sys.exit(1)
    
    # Unlock the vault
    if not bw.unlock():
        print("Failed to unlock Bitwarden vault")
        sys.exit(1)
    
    # Get secrets from Bitwarden
    secrets = bw.get_secrets(list(SECRET_MAPPING.keys()))
    
    if not secrets:
        print("No secrets found in Bitwarden")
        sys.exit(1)
    
    # Update .env file
    env_manager.update_env(secrets)
    
    print("\n=== Secrets Updated Successfully ===")
    print(f"Updated {len(secrets)} secrets in {ENV_FILE}")
    print("\nNote: Make sure to keep your .env file secure and never commit it to version control.")

if __name__ == "__main__":
    main()
