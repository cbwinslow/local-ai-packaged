#!/usr/bin/env python3
"""
Fetch Secrets from Bitwarden

This script securely fetches secrets from Bitwarden and updates environment variables.
It supports multiple environments and includes validation and error handling.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("secrets_manager.log"),
    ],
)
logger = logging.getLogger(__name__)


class Environment(str, Enum):
    """Supported environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class SecretCategory(str, Enum):
    """Categories for organizing secrets."""
    AUTH = "authentication"
    DATABASE = "database"
    AI = "ai_services"
    MONITORING = "monitoring"
    EXTERNAL = "external_services"
    SECURITY = "security"
    FEATURE_FLAGS = "feature_flags"


@dataclass
class SecretConfig:
    """Configuration for a secret."""
    item_name: str
    category: str
    required: bool = True
    sensitive: bool = True
    default: Optional[str] = None


# Configuration
ENV_FILE = ".env"
BW_CLI = "bw"
REQUIRED_ENV_VARS = {
    "NODE_ENV",
    "NEXT_PUBLIC_SUPABASE_URL",
    "NEXT_PUBLIC_SUPABASE_ANON_KEY",
    "SUPABASE_SERVICE_ROLE_KEY",
    "JWT_SECRET",
    "NEXTAUTH_SECRET",
    "NEXTAUTH_URL",
}

# Map of environment variables to Bitwarden item names and metadata
SECRET_MAPPING: Dict[str, SecretConfig] = {
    # Application
    "NODE_ENV": SecretConfig(
        item_name="Node Environment",
        category="application",
        required=True,
        sensitive=False,
        default="development",
    ),
    # Supabase
    "NEXT_PUBLIC_SUPABASE_URL": SecretConfig(
        item_name="Supabase Project URL",
        category=SecretCategory.DATABASE,
        required=True,
        sensitive=False,
    ),
    "NEXT_PUBLIC_SUPABASE_ANON_KEY": SecretConfig(
        item_name="Supabase Anon Key",
        category=SecretCategory.AUTH,
        required=True,
        sensitive=True,
    ),
    "SUPABASE_SERVICE_ROLE_KEY": SecretConfig(
        item_name="Supabase Service Role Key",
        category=SecretCategory.AUTH,
        required=True,
        sensitive=True,
    ),
    # Authentication
    "JWT_SECRET": SecretConfig(
        item_name="JWT Secret Key",
        category=SecretCategory.SECURITY,
        required=True,
        sensitive=True,
    ),
    "NEXTAUTH_SECRET": SecretConfig(
        item_name="NextAuth Secret",
        category=SecretCategory.SECURITY,
        required=True,
        sensitive=True,
    ),
    "NEXTAUTH_URL": SecretConfig(
        item_name="NextAuth URL",
        category=SecretCategory.AUTH,
        required=True,
        sensitive=False,
        default="http://localhost:3000",
    ),
    # Database
    "DATABASE_URL": SecretConfig(
        item_name="Database Connection String",
        category=SecretCategory.DATABASE,
        required=False,
        sensitive=True,
    ),
    # AI Services
    "OPENAI_API_KEY": SecretConfig(
        item_name="OpenAI API Key",
        category=SecretCategory.AI,
        required=False,
        sensitive=True,
    ),
    "ANTHROPIC_API_KEY": SecretConfig(
        item_name="Anthropic API Key",
        category=SecretCategory.AI,
        required=False,
        sensitive=True,
    ),
    # Monitoring
    "GRAFANA_ADMIN_PASSWORD": SecretConfig(
        item_name="Grafana Admin Password",
        category=SecretCategory.MONITORING,
        required=False,
        sensitive=True,
    ),
    # External Services
    "LINEAR_API_KEY": SecretConfig(
        item_name="Linear API Key",
        category=SecretCategory.EXTERNAL,
        required=False,
        sensitive=True,
    ),
    "GITHUB_TOKEN": SecretConfig(
        item_name="GitHub Personal Access Token",
        category=SecretCategory.EXTERNAL,
        required=False,
        sensitive=True,
    ),
    # Security
    "ENCRYPTION_KEY": SecretConfig(
        item_name="Application Encryption Key",
        category=SecretCategory.SECURITY,
        required=False,
        sensitive=True,
    ),
    # Feature Flags
    "ENABLE_EXPERIMENTAL_FEATURES": SecretConfig(
        item_name="Enable Experimental Features",
        category=SecretCategory.FEATURE_FLAGS,
        required=False,
        sensitive=False,
        default="false",
    ),
    "ENABLE_ANALYTICS": SecretConfig(
        item_name="Enable Analytics",
        category=SecretCategory.FEATURE_FLAGS,
        required=False,
        sensitive=False,
        default="false",
    ),
}


class BitwardenManager:
    """Manages interactions with the Bitwarden CLI."""

    def __init__(self) -> None:
        """Initialize the Bitwarden manager."""
        self.bw_path: str = self._find_bw()
        self.session: Optional[str] = None
        logger.info("Bitwarden CLI found at: %s", self.bw_path)

    def _find_bw(self) -> str:
        """Find the Bitwarden CLI executable."""
        try:
            result = subprocess.run(
                ["which", "bw"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error("Bitwarden CLI not found. Please install it first.")
            sys.exit(1)

    def _run_bw_command(
        self, command: str, args: list[str] | None = None, session: bool = True
    ) -> dict[str, Any]:
        """Run a Bitwarden CLI command.

        Args:
            command: The Bitwarden CLI command to run
            args: List of arguments to pass to the command
            session: Whether to use the current session

        Returns:
            Dict containing the command output
        """
        if args is None:
            args = []

        cmd = [self.bw_path, command] + args
        if session and self.session:
            cmd.extend(["--session", self.session])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            if result.stdout.strip():
                return json.loads(result.stdout)
            return {}
        except subprocess.CalledProcessError as e:
            logger.error("Error running Bitwarden command: %s", e.stderr)
            raise
        except json.JSONDecodeError as e:
            logger.error("Failed to parse Bitwarden output: %s", e)
            return {}

    def login(self) -> bool:
        """Log in to Bitwarden.

        Returns:
            bool: True if login was successful, False otherwise
        """
        try:
            # Check if already logged in
            status = self._run_bw_command("status")
            if status.get("status") == "unlocked":
                logger.info("Already logged in to Bitwarden")
                return True
            
            # Start interactive login
            logger.info("Logging in to Bitwarden...")
            print("\n=== Bitwarden Login ===")
            print("Please check your email for the verification code.\n")
            
            # Start login process
            result = subprocess.run(
                [self.bw_path, "login", "--raw"],
                capture_output=True,
                text=True,
                check=True,
            )
            
            self.session = result.stdout.strip()
            logger.info("Successfully logged in to Bitwarden")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error("Failed to log in to Bitwarden: %s", e.stderr)
            return False
    
    def unlock(self, password: str) -> bool:
        """Unlock the Bitwarden vault.
        
        Args:
            password: Master password for the vault
            
        Returns:
            bool: True if unlock was successful, False otherwise
        """
        try:
            result = subprocess.run(
                [self.bw_path, "unlock", "--passwordenv", "BW_PASSWORD", "--raw"],
                env={"BW_PASSWORD": password, **os.environ},
                capture_output=True,
                text=True,
                check=True,
            )
            self.session = result.stdout.strip()
            logger.info("Successfully unlocked Bitwarden vault")
            return True
        except subprocess.CalledProcessError as e:
            logger.error("Failed to unlock Bitwarden vault: %s", e.stderr)
            return False
    
    def get_secret(self, item_name: str, field_name: Optional[str] = None) -> Optional[str]:
        """Get a secret from Bitwarden.
        
        Args:
            item_name: Name of the item in Bitwarden
            field_name: Name of the field to retrieve (defaults to password)
            
        Returns:
            The secret value or None if not found
        """
        try:
            # First, search for the item
            search_cmd = [self.bw_path, "list", "items", "--search", item_name]
            if self.session:
                search_cmd.extend(["--session", self.session])
                
            result = subprocess.run(
                search_cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            
            items = json.loads(result.stdout)
            if not items:
                logger.warning("No items found matching: %s", item_name)
                return None
                
            # Get the first matching item
            item = items[0]
            item_id = item["id"]
            
            # Get the item details
            get_cmd = [self.bw_path, "get", "item", item_id]
            if self.session:
                get_cmd.extend(["--session", self.session])
                
            result = subprocess.run(
                get_cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            
            item_details = json.loads(result.stdout)
            
            # Get the field value
            if field_name:
                # Look in fields
                for field in item_details.get("fields", []):
                    if field.get("name", "").lower() == field_name.lower():
                        return field.get("value")
                
                # Look in login
                if "login" in item_details and field_name.lower() in ["username", "password"]:
                    return item_details["login"].get(field_name.lower())

                logger.warning("Field '%s' not found in item: %s", field_name, item_name)
                return None
            else:
                # Default to password if no field specified
                return item_details.get("login", {}).get("password")

        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as e:
            logger.error("Error retrieving secret for %s: %s", item_name, str(e))
            return None


class EnvManager:
    """Manages environment variables and .env files."""

    def __init__(self, env_file: str = ".env") -> None:
        """Initialize the environment manager.
        
        Args:
            env_file: Path to the .env file
        """
        self.env_file = Path(env_file)
        self.env_vars: dict[str, str] = {}
        self.load_env()
    
    def load_env(self) -> dict[str, str]:
        """Load environment variables from .env file.

        Returns:
            Dict of environment variables
        """
        self.env_vars = {}

        if not self.env_file.exists():
            logger.warning("No .env file found at %s", self.env_file)
            return {}

        try:
            with open(self.env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    # Parse key=value pairs
                    if "=" in line:
                        key, value = line.split("=", 1)
                        self.env_vars[key.strip()] = value.strip('"\'')

        except IOError as e:
            logger.error("Error reading .env file: %s", e)

        return self.env_vars

    def update_env(self, updates: dict[str, str]) -> int:
        """Update environment variables in the .env file.

        Args:
            updates: Dict of key-value pairs to update

        Returns:
            Number of variables updated
        """
        updated = 0

        # Update in-memory variables
        for key, value in updates.items():
            if key in self.env_vars and self.env_vars[key] == value:
                continue

            self.env_vars[key] = value
            updated += 1

        if not updated:
            logger.info("No environment variables to update")
            return 0

        # Create backup of existing file
        if self.env_file.exists():
            backup_file = f"{self.env_file}.bak"
            try:
                import shutil
                shutil.copy2(self.env_file, backup_file)
                logger.info("Created backup at %s", backup_file)
            except IOError as e:
                logger.error("Failed to create backup: %s", e)

        # Write updated variables to file
        try:
            with open(self.env_file, "w", encoding="utf-8") as f:
                for key, value in self.env_vars.items():
                    if value is None:
                        continue
                    f.write(f"{key}=\"{value}\"\n")

            logger.info("Updated %d environment variables in %s", updated, self.env_file)
            return updated

        except IOError as e:
            logger.error("Error writing to .env file: %s", e)
            return 0


def fetch_secrets(env: str = "development") -> int:
    """Fetch secrets from Bitwarden and update .env file.

    Args:
        env: Environment to fetch secrets for (development, staging, production)
        
    Returns:
        Number of secrets updated
    """
    try:
        # Initialize managers
        bw = BitwardenManager()
        env_manager = EnvManager()
        
        # Login to Bitwarden if needed
        if not bw.login():
            logger.error("Failed to log in to Bitwarden")
            return 0
            
        # Unlock the vault (will prompt for password)
        import getpass
        password = getpass.getpass("Enter your Bitwarden master password: ")
        if not bw.unlock(password):
            logger.error("Failed to unlock Bitwarden vault")
            return 0
        
        # Fetch secrets
        updates = {}
        for var_name, config in SECRET_MAPPING.items():
            # Skip if not required and not in required vars
            if not config.required and var_name not in REQUIRED_ENV_VARS:
                continue
                
            # Skip if already set and not forced
            if var_name in os.environ and not os.getenv("FORCE_UPDATE"):
                logger.debug("Skipping %s (already set)", var_name)
                continue
                
            # Get the secret from Bitwarden
            secret = bw.get_secret(config.item_name)
            if secret is None and config.required:
                logger.warning("Required secret not found: %s", config.item_name)
                if config.default is not None:
                    logger.info("Using default value for %s", var_name)
                    secret = config.default
                else:
                    logger.error("No default value for required secret: %s", var_name)
                    continue
            
            updates[var_name] = secret
        
        # Update .env file
        if updates:
            updated = env_manager.update_env(updates)
            logger.info("Successfully updated %d secrets", updated)
            return updated
        else:
            logger.info("No secrets to update")
            return 0
            
    except Exception as e:
        logger.exception("Error fetching secrets: %s", e)
        return 0


def main() -> None:
    """Main entry point for the script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fetch secrets from Bitwarden and update .env file")
    parser.add_argument(
        "--env", 
        choices=[e.value for e in Environment], 
        default="development",
        help="Environment to fetch secrets for"
    )
    parser.add_argument(
        "--force", 
        action="store_true",
        help="Force update all variables, even if they already exist"
    )
    parser.add_argument(
        "--debug", 
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("secrets_manager.log"),
        ],
    )
    
    # Set FORCE_UPDATE environment variable
    if args.force:
        os.environ["FORCE_UPDATE"] = "1"
    
    # Fetch secrets
    updated = fetch_secrets(args.env)
    if updated == 0:
        logger.warning("No secrets were updated")
        sys.exit(1)
    
    logger.info("Done!")
    sys.exit(0)


if __name__ == "__main__":
    main()
