#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys
from pathlib import Path
import shutil
import re
from datetime import datetime

try:
    import getpass
except ImportError:
    # This will be handled gracefully later if needed.
    getpass = None

# Color codes for output
class Colors:
    """ANSI color codes for console output."""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    NC = '\033[0m'

def check_bw_cli():
    """Check if Bitwarden CLI is installed."""
    if not shutil.which("bw"):
        print(f"{Colors.RED}❌ Bitwarden CLI (bw) not found.{Colors.NC}")
        print("Please install it from: https://bitwarden.com/help/cli/")
        sys.exit(1)
    print(f"{Colors.GREEN}✔ Bitwarden CLI found.{Colors.NC}")

def unlock_vault():
    """Unlock Bitwarden vault if BW_SESSION is not set. Returns True on success, False on failure."""
    if os.getenv('BW_SESSION'):
        print(f"{Colors.GREEN}✔ Bitwarden vault already unlocked.{Colors.NC}")
        return True

    print("🔐 Unlocking Bitwarden vault...")
    password = os.getenv('BW_PASSWORD')
    if not password:
        if not getpass:
            print(f"{Colors.RED}❌ 'getpass' module not available. Cannot prompt for password.{Colors.NC}")
            print("Please set the BW_PASSWORD environment variable.")
            sys.exit(1)
        try:
            password = getpass.getpass("Enter Bitwarden master password: ")
        except (EOFError, KeyboardInterrupt):
            print("\nOperation cancelled by user.")
            sys.exit(1)

    try:
        process = subprocess.run(
            ['bw', 'unlock', '--raw'],
            input=password,
            text=True,
            capture_output=True,
            check=True
        )
        os.environ['BW_SESSION'] = process.stdout.strip()
        print(f"{Colors.GREEN}✔ Vault unlocked successfully.{Colors.NC}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}❌ Failed to unlock Bitwarden vault.{Colors.NC}")
        print(f"Error details: {e.stderr.strip()}", file=sys.stderr)
        return False

def get_secret_from_bw(name, prefix):
    """Fetch a secret from Bitwarden."""
    bw_name = f"{prefix}{name.lower()}"
    try:
        process = subprocess.run(
            ['bw', 'get', 'password', bw_name],
            capture_output=True,
            text=True,
            check=False,
            env=os.environ
        )
        if process.returncode == 0:
            return process.stdout.strip()
        if "No item found" in process.stderr:
            return None
        else:
            print(f"{Colors.YELLOW}⚠️  Bitwarden CLI error for '{bw_name}': {process.stderr.strip()}{Colors.NC}", file=sys.stderr)
            return None
    except Exception as e:
        print(f"{Colors.RED}❌ An error occurred while fetching secret '{bw_name}': {e}{Colors.NC}", file=sys.stderr)
        return None

def generate_secret(variable_name, dependencies):
    """
    Generate a secret by calling the corresponding function in generate-secrets.sh,
    but only if the generation function exists.
    """
    script_path = Path(__file__).parent / 'generate-secrets.sh'
    if not script_path.exists():
        print(f"{Colors.RED}❌ Generation script not found at {script_path}{Colors.NC}", file=sys.stderr)
        return None

    function_name = f"generate_{variable_name.lower()}"

    # Check if the function exists in the shell script
    check_command = f"source {script_path} && type {function_name}"
    check_process = subprocess.run(['bash', '-c', check_command], capture_output=True, text=True)

    if check_process.returncode != 0:
        # The generation function does not exist, which is expected for user-provided API keys.
        print(f"    {Colors.YELLOW}- No generation function for '{variable_name}'. Skipping.{Colors.NC}")
        return None

    # The function exists, so we can proceed with generation
    command = f"source {script_path} && {function_name} {' '.join(dependencies)}"
    try:
        process = subprocess.run(
            ['bash', '-c', command],
            capture_output=True,
            text=True,
            check=True
        )
        return process.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}❌ Failed to generate secret for {variable_name}: {e.stderr.strip()}{Colors.NC}", file=sys.stderr)
        return None

def main():
    """Main function to orchestrate secret population."""
    parser = argparse.ArgumentParser(
        description="Populate .env file from a Bitwarden vault, with an option to generate missing secrets.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('--env-file', type=Path, default=Path('.env'), help='Path to the output .env file. Default: ./.env')
    parser.add_argument('--template-file', type=Path, default=Path('.env.example'), help='Path to the template file. Default: ./.env.example')
    parser.add_argument('--bw-prefix', type=str, default='localai_', help='Prefix for Bitwarden secret names. Default: localai_')
    parser.add_argument('--generate-missing', action='store_true', help='Generate secrets for entries not found in Bitwarden.')
    parser.add_argument('--force', action='store_true', help='Overwrite existing .env file without creating a backup.')
    args = parser.parse_args()

    check_bw_cli()
    vault_unlocked = unlock_vault()

    if not vault_unlocked:
        print(f"{Colors.YELLOW}⚠️  Could not unlock vault. Will not fetch secrets from Bitwarden.{Colors.NC}")
        if not args.generate_missing:
            print(f"{Colors.RED}❌ Aborting because vault is locked and --generate-missing is not set.{Colors.NC}", file=sys.stderr)
            sys.exit(1)

    if not args.template_file.exists():
        print(f"{Colors.RED}❌ Template file not found: {args.template_file}{Colors.NC}", file=sys.stderr)
        sys.exit(1)

    if args.env_file.exists() and not args.force:
        backup_path = Path(f"{args.env_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        print(f"Backing up existing {args.env_file} to {backup_path}")
        shutil.copy(args.env_file, backup_path)

    print(f"Reading template from {args.template_file}...")
    with open(args.template_file, 'r') as f:
        template_lines = f.readlines()

    final_env_content = []
    env_vars = {}

    secret_vars = {
        line.split('=', 1)[0].strip()
        for line in template_lines
        if '=' in line and line.split('=', 1)[1].strip() == '' and not line.strip().startswith('#')
    }

    print("Processing environment variables...")
    for line in template_lines:
        line_strip = line.strip()
        if not line_strip or line_strip.startswith('#'):
            final_env_content.append(line)
            continue

        match = re.match(r'([^=]+)=(.*)', line)
        if not match:
            final_env_content.append(line)
            continue

        var_name = match.group(1).strip()
        default_value = match.group(2).strip()

        if var_name not in secret_vars:
            final_env_content.append(line)
            env_vars[var_name] = default_value
            continue

        print(f"  - Processing secret '{var_name}'...")

        value = None
        if vault_unlocked:
            # Handle special cases where the .env var name differs from the BW item name
            bw_lookup_var = 'neo4j_password' if var_name == 'NEO4J_AUTH' else var_name
            value = get_secret_from_bw(bw_lookup_var, args.bw_prefix)

        if value:
            # Construct composite variables
            if var_name == 'NEO4J_AUTH':
                value = f"neo4j/{value}"
            print(f"    {Colors.GREEN}✔ Found in Bitwarden.{Colors.NC}")
            env_vars[var_name] = value
        elif args.generate_missing:
            print(f"    {Colors.YELLOW}⚠️  Not found in Bitwarden. Generating...{Colors.NC}")

            dependencies = []
            if var_name in ['ANON_KEY', 'SERVICE_ROLE_KEY']:
                if 'JWT_SECRET' not in env_vars:
                    print(f"    {Colors.RED}❌ Cannot generate {var_name} without JWT_SECRET.{Colors.NC}", file=sys.stderr)
                    value = "GENERATION_FAILED_MISSING_JWT_SECRET"
                else:
                    dependencies.append(f'"{env_vars["JWT_SECRET"]}"')

            gen_var_name = 'neo4j_password' if var_name == 'NEO4J_AUTH' else var_name
            generated_part = generate_secret(gen_var_name, dependencies) if not value else None

            if generated_part:
                value = f"neo4j/{generated_part}" if var_name == 'NEO4J_AUTH' else generated_part
                print(f"    {Colors.GREEN}✔ Generated successfully.{Colors.NC}")
            else:
                value = f"GENERATION_FAILED_{var_name}"
                print(f"    {Colors.RED}❌ Generation failed.{Colors.NC}")
            env_vars[var_name] = value
        else:
            print(f"    {Colors.YELLOW}⚠️  Not found in Bitwarden and not generating. Using placeholder.{Colors.NC}")
            env_vars[var_name] = f"BITWARDEN_SECRET_MISSING_{var_name}"

        final_value = env_vars.get(var_name, "")
        # Quote value if it contains spaces or special characters
        if any(c in final_value for c in ' "#'):
            final_value = f'"{final_value}"'

        final_env_content.append(f"{var_name}={final_value}\n")

    print(f"Writing final .env file to {args.env_file}...")
    with open(args.env_file, 'w') as f:
        f.writelines(final_env_content)

    print(f"\n{Colors.GREEN}✅ .env file created successfully.{Colors.NC}")
    print(f"Processed {len(env_vars)} variables.")

if __name__ == "__main__":
    main()