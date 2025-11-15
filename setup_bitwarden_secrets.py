#!/usr/bin/env python3
"""
Bitwarden Secrets Setup Script for Local AI Package

This script fetches secrets from Bitwarden vault and creates a .env file.
It searches for secrets using multiple naming patterns:
  - Exact name (e.g., 'N8N_ENCRYPTION_KEY')
  - user.account.<name> (e.g., 'user.account.N8N_ENCRYPTION_KEY')
  - user.secret.<name> (e.g., 'user.secret.N8N_ENCRYPTION_KEY')
  - machine.account.<name> (e.g., 'machine.account.N8N_ENCRYPTION_KEY')
"""

import json
import os
import subprocess
import sys
import shutil
from typing import Optional, List, Tuple

# ANSI color codes
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
NC = '\033[0m'  # No Color


def print_colored(message: str, color: str = NC):
    """Print colored message to console"""
    print(f"{color}{message}{NC}")


def check_bw_installed() -> bool:
    """Check if Bitwarden CLI is installed"""
    return shutil.which('bw') is not None


def run_command(command: List[str], capture_output: bool = True) -> Tuple[int, str, str]:
    """Run a shell command and return exit code, stdout, stderr"""
    try:
        result = subprocess.run(
            command,
            capture_output=capture_output,
            text=True,
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def check_bw_login() -> bool:
    """Check if user is logged into Bitwarden"""
    code, _, _ = run_command(['bw', 'login', '--check'])
    return code == 0


def unlock_vault() -> Optional[str]:
    """Unlock Bitwarden vault and return session token"""
    # Check if BW_SESSION is already set
    session = os.environ.get('BW_SESSION')
    if session:
        # Verify the session is still valid
        code, _, _ = run_command(['bw', 'sync', '--session', session])
        if code == 0:
            return session
    
    print("Please enter your master password to unlock the vault:")
    code, stdout, stderr = run_command(['bw', 'unlock', '--raw'], capture_output=True)
    
    if code == 0 and stdout.strip():
        return stdout.strip()
    
    print_colored(f"Error unlocking vault: {stderr}", RED)
    return None


def sync_vault(session: str) -> bool:
    """Sync Bitwarden vault"""
    code, _, _ = run_command(['bw', 'sync', '--session', session])
    return code == 0


def get_secret(secret_name: str, session: str) -> Optional[str]:
    """
    Search for a secret in Bitwarden using multiple naming patterns.
    Returns the secret value if found, None otherwise.
    """
    search_patterns = [
        secret_name,
        f"user.account.{secret_name}",
        f"user.secret.{secret_name}",
        f"machine.account.{secret_name}"
    ]
    
    for pattern in search_patterns:
        code, stdout, _ = run_command(['bw', 'get', 'item', pattern, '--session', session])
        
        if code == 0 and stdout.strip():
            try:
                item = json.loads(stdout)
                # Try to get password field first
                if 'login' in item and 'password' in item['login']:
                    password = item['login']['password']
                    if password:
                        return password
                
                # Try notes field
                if 'notes' in item and item['notes']:
                    return item['notes']
                
            except json.JSONDecodeError:
                continue
    
    return None


def update_env_file(secret_name: str, value: str):
    """Update .env file with secret value"""
    # Read the file
    with open('.env', 'r') as f:
        lines = f.readlines()
    
    # Update the lines
    updated = False
    for i, line in enumerate(lines):
        # Match both commented and uncommented lines
        if line.strip().startswith(f'{secret_name}=') or line.strip().startswith(f'# {secret_name}='):
            lines[i] = f'{secret_name}={value}\n'
            updated = True
            break
    
    # Write back
    with open('.env', 'w') as f:
        f.writelines(lines)


def main():
    """Main function"""
    print("=" * 50)
    print("Bitwarden Secrets Setup for Local AI Package")
    print("=" * 50)
    print()
    
    # Check if bw is installed
    if not check_bw_installed():
        print_colored("Error: Bitwarden CLI (bw) is not installed", RED)
        print()
        print("Please install it from: https://bitwarden.com/help/cli/")
        print()
        print("Installation instructions:")
        print("  npm install -g @bitwarden/cli")
        print("  Or download from: https://github.com/bitwarden/clients/releases")
        sys.exit(1)
    
    print_colored("✓ Bitwarden CLI found", GREEN)
    
    # Check if .env.example exists
    if not os.path.exists('.env.example'):
        print_colored("Error: .env.example not found", RED)
        print("Please run this script from the root of the local-ai-packaged repository")
        sys.exit(1)
    
    # Check login status
    print()
    print("Checking Bitwarden login status...")
    
    if not check_bw_login():
        print("Not logged in to Bitwarden. Please login:")
        print()
        print("Options:")
        print("  1. Login with email/password: bw login")
        print("  2. Login with API key: bw login --apikey")
        print()
        input("Press enter after logging in...")
        
        if not check_bw_login():
            print_colored("Error: Still not logged in to Bitwarden", RED)
            sys.exit(1)
    
    # Unlock vault
    print()
    print("Unlocking Bitwarden vault...")
    session = unlock_vault()
    
    if not session:
        print_colored("Error: Failed to unlock Bitwarden vault", RED)
        sys.exit(1)
    
    print_colored("✓ Vault unlocked", GREEN)
    
    # Sync vault
    print("Syncing vault...")
    if not sync_vault(session):
        print_colored("Warning: Failed to sync vault, continuing with cached data", YELLOW)
    else:
        print_colored("✓ Vault synced", GREEN)
    print()
    
    # Backup existing .env if it exists
    if os.path.exists('.env'):
        print_colored("Backing up existing .env to .env.backup", YELLOW)
        shutil.copy('.env', '.env.backup')
    
    # Start with .env.example as template
    shutil.copy('.env.example', '.env')
    
    print("Fetching secrets from Bitwarden vault...")
    print()
    
    # Track found and missing secrets
    found_secrets = []
    missing_secrets = []
    
    def fetch_and_update(secret_name: str, is_required: bool = True):
        """Fetch secret and update .env file"""
        print(f"  Fetching secret... ", end='', flush=True)
        value = get_secret(secret_name, session)
        
        if value:
            update_env_file(secret_name, value)
            print_colored("✓", GREEN)
            found_secrets.append(secret_name)
            return True
        else:
            print_colored("✗", RED)
            if is_required:
                missing_secrets.append(secret_name)
            return False
    
    # Required N8N secrets
    print_colored("N8N Configuration:", YELLOW)
    fetch_and_update("N8N_ENCRYPTION_KEY", True)
    fetch_and_update("N8N_USER_MANAGEMENT_JWT_SECRET", True)
    print()
    
    # Required Supabase secrets
    print_colored("Supabase Secrets:", YELLOW)
    fetch_and_update("POSTGRES_PASSWORD", True)
    fetch_and_update("JWT_SECRET", True)
    fetch_and_update("ANON_KEY", True)
    fetch_and_update("SERVICE_ROLE_KEY", True)
    fetch_and_update("DASHBOARD_USERNAME", True)
    fetch_and_update("DASHBOARD_PASSWORD", True)
    fetch_and_update("POOLER_TENANT_ID", True)
    print()
    
    # Required Neo4j secrets
    print_colored("Neo4j Secrets:", YELLOW)
    fetch_and_update("NEO4J_AUTH", True)
    print()
    
    # Required Langfuse secrets
    print_colored("Langfuse Credentials:", YELLOW)
    fetch_and_update("CLICKHOUSE_PASSWORD", True)
    fetch_and_update("MINIO_ROOT_PASSWORD", True)
    fetch_and_update("LANGFUSE_SALT", True)
    fetch_and_update("NEXTAUTH_SECRET", True)
    fetch_and_update("ENCRYPTION_KEY", True)
    print()
    
    # Optional additional secrets
    print_colored("Additional Secrets:", YELLOW)
    fetch_and_update("SECRET_KEY_BASE", False)
    fetch_and_update("VAULT_ENC_KEY", False)
    print()
    
    # Optional production secrets
    print_colored("Optional Production Configuration:", YELLOW)
    fetch_and_update("N8N_HOSTNAME", False)
    fetch_and_update("WEBUI_HOSTNAME", False)
    fetch_and_update("FLOWISE_HOSTNAME", False)
    fetch_and_update("SUPABASE_HOSTNAME", False)
    fetch_and_update("OLLAMA_HOSTNAME", False)
    fetch_and_update("SEARXNG_HOSTNAME", False)
    fetch_and_update("NEO4J_HOSTNAME", False)
    fetch_and_update("LETSENCRYPT_EMAIL", False)
    print()
    
    # Summary
    print("=" * 50)
    print("Summary")
    print("=" * 50)
    print()
    print_colored(f"Found secrets: {len(found_secrets)}", GREEN)
    print_colored(f"Missing required secrets: {len(missing_secrets)}", RED)
    print()
    
    if missing_secrets:
        print_colored("⚠ WARNING: The following required secrets are missing:", RED)
        for secret in missing_secrets:
            print(f"  - {secret}")
        print()
        print("Please add these secrets to your Bitwarden vault using one of these naming patterns:")
        print("  - Exact name (e.g., 'N8N_ENCRYPTION_KEY')")
        print("  - user.account.<name> (e.g., 'user.account.N8N_ENCRYPTION_KEY')")
        print("  - user.secret.<name> (e.g., 'user.secret.N8N_ENCRYPTION_KEY')")
        print("  - machine.account.<name> (e.g., 'machine.account.N8N_ENCRYPTION_KEY')")
        print()
        print("Store the secret value in the 'Password' field of the Bitwarden item.")
        print()
        print_colored("The .env file has been created but is INCOMPLETE.", YELLOW)
        print("Please add the missing secrets to Bitwarden and run this script again.")
        sys.exit(1)
    else:
        print_colored("✓ All required secrets found and configured!", GREEN)
        print()
        print("The .env file has been created successfully.")
        print("You can now run: python start_services.py --profile <your-profile>")
        print()
    
    # Security reminder
    print("=" * 50)
    print_colored("Security Reminder:", YELLOW)
    print("  - The .env file is listed in .gitignore")
    print("  - Never commit the .env file to version control")
    print("  - Keep your Bitwarden master password secure")
    print("=" * 50)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_colored("Operation cancelled by user", YELLOW)
        sys.exit(1)
    except Exception as e:
        print_colored(f"An unexpected error occurred: {e}", RED)
        sys.exit(1)
