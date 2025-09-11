#!/usr/bin/env python3
"""
Test Secret Generation and Environment Configuration
Tests the security and completeness of secret generation
"""

import pytest
import os
import subprocess
import tempfile
import shutil
from pathlib import Path
import re
import urllib.parse

class TestSecretGeneration:
    """Test secret generation and environment configuration"""
    
    @pytest.fixture
    def project_root(self):
        """Get project root directory"""
        return Path(__file__).parent.parent
    
    @pytest.fixture
    def temp_env_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_env_template_exists(self, project_root):
        """Test that .env.template exists"""
        env_template = project_root / ".env.template"
        assert env_template.exists(), ".env.template file not found"
        
        # Check it's not empty
        content = env_template.read_text()
        assert len(content) > 100, ".env.template appears to be empty or too small"
    
    def test_secret_generation_script_exists(self, project_root):
        """Test that secret generation script exists and is executable"""
        script_path = project_root / "scripts" / "generate-secrets.sh"
        assert script_path.exists(), "Secret generation script not found"
        
        # Check if it's executable
        assert os.access(script_path, os.X_OK), "Secret generation script is not executable"
    
    def test_env_template_variables(self, project_root):
        """Test that .env.template contains required variables"""
        env_template = project_root / ".env.template"
        content = env_template.read_text()
        
        required_vars = [
            "POSTGRES_PASSWORD",
            "JWT_SECRET",
            "ANON_KEY",
            "SERVICE_ROLE_KEY",
            "N8N_ENCRYPTION_KEY",
            "N8N_USER_MANAGEMENT_JWT_SECRET",
            "ENCRYPTION_KEY",
            "NEXTAUTH_SECRET"
        ]
        
        missing_vars = []
        for var in required_vars:
            if var not in content:
                missing_vars.append(var)
        
        assert not missing_vars, f"Missing required variables in .env.template: {missing_vars}"
    
    def test_no_hardcoded_secrets_in_template(self, project_root):
        """Test that .env.template doesn't contain actual secrets"""
        env_template = project_root / ".env.template"
        content = env_template.read_text()
        
        # Pattern for actual secrets (base64, hex, etc.)
        secret_patterns = [
            r'[A-Za-z0-9+/]{20,}={0,2}',  # Base64-like
            r'[a-f0-9]{32,}',             # Hex strings
            r'eyJ[A-Za-z0-9+/]+=*',       # JWT tokens
        ]
        
        suspicious_lines = []
        for line_num, line in enumerate(content.split('\n'), 1):
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.split('=', 1)
                value = value.strip()
                
                # Skip placeholder values
                if value.startswith('your-') or value in ['', 'placeholder', 'test']:
                    continue
                
                # Check for secret patterns
                for pattern in secret_patterns:
                    if re.match(pattern, value) and len(value) > 10:
                        suspicious_lines.append(f"Line {line_num}: {key}")
        
        assert not suspicious_lines, f"Potential hardcoded secrets found: {suspicious_lines}"
    
    def test_secret_generation_dry_run(self, project_root, temp_env_dir):
        """Test secret generation script in dry-run mode"""
        # Copy .env.template to temp directory
        env_template = project_root / ".env.template"
        temp_env = temp_env_dir / ".env"
        shutil.copy(env_template, temp_env)
        
        # Run secret generation script
        script_path = project_root / "scripts" / "generate-secrets.sh"
        
        try:
            result = subprocess.run(
                [str(script_path), "--env-file", str(temp_env)],
                cwd=temp_env_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Should complete successfully
            assert result.returncode == 0, f"Secret generation failed: {result.stderr}"
            
            # Check that .env file was modified
            env_content = temp_env.read_text()
            assert "your-" not in env_content.lower(), "Template placeholders still present after generation"
            
        except subprocess.TimeoutExpired:
            pytest.fail("Secret generation script timed out")
        except FileNotFoundError:
            pytest.skip("Secret generation script requires bash/openssl")
    
    def test_generated_secrets_quality(self, project_root, temp_env_dir):
        """Test the quality of generated secrets"""
        # Copy .env.template to temp directory
        env_template = project_root / ".env.template"
        temp_env = temp_env_dir / ".env"
        shutil.copy(env_template, temp_env)
        
        # Run secret generation script
        script_path = project_root / "scripts" / "generate-secrets.sh"
        
        try:
            result = subprocess.run(
                [str(script_path), "--env-file", str(temp_env)],
                cwd=temp_env_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                pytest.skip("Secret generation failed")
            
            env_content = temp_env.read_text()
            
            # Parse environment variables
            env_vars = {}
            for line in env_content.split('\n'):
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
            
            # Test secret quality
            secret_vars = [var for var in env_vars.keys() 
                          if any(word in var.lower() for word in ['password', 'secret', 'key', 'token'])]
            
            weak_secrets = []
            for var in secret_vars:
                value = env_vars.get(var, '')
                
                # Skip special formats like neo4j auth
                if var == 'NEO4J_AUTH':
                    continue
                
                # Check minimum length
                if len(value) < 16:
                    weak_secrets.append(f"{var}: too short ({len(value)} chars)")
                
                # Check for complexity (at least some variation)
                if len(set(value)) < 8:
                    weak_secrets.append(f"{var}: insufficient complexity")
            
            assert not weak_secrets, f"Weak secrets generated: {weak_secrets}"
            
        except subprocess.TimeoutExpired:
            pytest.skip("Secret generation script timed out")
        except FileNotFoundError:
            pytest.skip("Secret generation script requires bash/openssl")
    
    def test_fix_supabase_env_redirect(self, project_root):
        """Test that fix-supabase-env.sh redirects to comprehensive script"""
        script_path = project_root / "fix-supabase-env.sh"
        
        if script_path.exists():
            content = script_path.read_text()
            
            # Should reference the comprehensive script
            assert "generate-secrets.sh" in content, "fix-supabase-env.sh should redirect to generate-secrets.sh"
            assert "deprecated" in content.lower(), "fix-supabase-env.sh should indicate it's deprecated"
    
    def test_domain_configuration(self, project_root):
        """Test domain configuration for opendiscourse.net"""
        env_template = project_root / ".env.template"
        content = env_template.read_text()
        
        # Should contain opendiscourse.net references in values, not just comments
        lines = [line for line in content.split('\n') if line.strip() and not line.strip().startswith('#') and '=' in line]
        def is_opendiscourse_domain(value):
            value = value.strip()
            # Check if value is a URL
            try:
                parsed = urllib.parse.urlparse(value)
                host = parsed.hostname
                if host and (host == "opendiscourse.net" or host.endswith(".opendiscourse.net")):
                    return True
            except Exception:
                pass
            # Otherwise, check direct domain match
            if value == "opendiscourse.net" or value.endswith(".opendiscourse.net"):
                return True
            return False

        found = any(
            is_opendiscourse_domain(line.split('=', 1)[1]) for line in lines
        )
        assert found, ".env.template should contain opendiscourse.net domain in a configuration value"
        
        # Should not contain old domain placeholders
        old_domains = ["yourdomain.com", "example.com", "localhost.com"]
        for domain in old_domains:
            if domain in content:
                # Count occurrences in comments vs actual values
                lines = content.split('\n')
                actual_usage = sum(1 for line in lines 
                                 if domain in line and not line.strip().startswith('#') and '=' in line)
                if actual_usage > 0:
                    pytest.fail(f"Old domain placeholder '{domain}' found in actual configuration")

if __name__ == "__main__":
    pytest.main([__file__])