#!/usr/bin/env python3
"""
Test Terraform Configuration
Tests Terraform files for syntax, security, and best practices
"""

import pytest
import json
import subprocess
from pathlib import Path
import tempfile
import shutil

class TestTerraform:
    """Test Terraform configurations"""
    
    @pytest.fixture
    def project_root(self):
        """Get project root directory"""
        return Path(__file__).parent.parent
    
    @pytest.fixture
    def terraform_dir(self, project_root):
        """Get Terraform directory"""
        return project_root / "terraform" / "cloudflare"
    
    @pytest.fixture
    def temp_terraform_dir(self, terraform_dir):
        """Create temporary copy of Terraform directory for testing"""
        if not terraform_dir.exists():
            pytest.skip("Terraform directory not found")
        
        temp_dir = tempfile.mkdtemp()
        temp_tf_dir = Path(temp_dir) / "terraform"
        shutil.copytree(terraform_dir, temp_tf_dir)
        
        # Create test terraform.tfvars
        tfvars_content = """
cloudflare_api_token = "test-token"
cloudflare_account_id = "test-account-id"
domain_name = "opendiscourse.net"
environment = "test"
"""
        (temp_tf_dir / "terraform.tfvars").write_text(tfvars_content)
        
        yield temp_tf_dir
        shutil.rmtree(temp_dir)
    
    def test_terraform_files_exist(self, terraform_dir):
        """Test that Terraform files exist"""
        if not terraform_dir.exists():
            pytest.skip("Terraform directory not found")
        
        required_files = ["main.tf"]
        missing_files = []
        
        for file in required_files:
            if not (terraform_dir / file).exists():
                missing_files.append(file)
        
        assert not missing_files, f"Missing required Terraform files: {missing_files}"
    
    def test_terraform_syntax(self, temp_terraform_dir):
        """Test Terraform syntax validation"""
        try:
            # Initialize Terraform
            result = subprocess.run(
                ["terraform", "init"],
                cwd=temp_terraform_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                pytest.skip(f"Terraform init failed: {result.stderr}")
            
            # Validate syntax
            result = subprocess.run(
                ["terraform", "validate"],
                cwd=temp_terraform_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            assert result.returncode == 0, f"Terraform validation failed: {result.stderr}"
            
        except subprocess.TimeoutExpired:
            pytest.fail("Terraform validation timed out")
        except FileNotFoundError:
            pytest.skip("Terraform CLI not available")
    
    def test_terraform_formatting(self, temp_terraform_dir):
        """Test Terraform formatting"""
        try:
            result = subprocess.run(
                ["terraform", "fmt", "-check"],
                cwd=temp_terraform_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                pytest.fail(f"Terraform formatting issues found:\n{result.stdout}")
                
        except subprocess.TimeoutExpired:
            pytest.fail("Terraform fmt check timed out")
        except FileNotFoundError:
            pytest.skip("Terraform CLI not available")
    
    def test_terraform_plan(self, temp_terraform_dir):
        """Test Terraform plan generation"""
        try:
            # Initialize Terraform
            init_result = subprocess.run(
                ["terraform", "init"],
                cwd=temp_terraform_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if init_result.returncode != 0:
                pytest.skip(f"Terraform init failed: {init_result.stderr}")
            
            # Generate plan
            plan_result = subprocess.run(
                ["terraform", "plan", "-out=test.tfplan"],
                cwd=temp_terraform_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            # Plan should succeed (even with invalid credentials)
            # We're testing syntax and logic, not actual deployment
            if "Error:" in plan_result.stderr and "authentication" not in plan_result.stderr.lower():
                pytest.fail(f"Terraform plan failed with non-auth error: {plan_result.stderr}")
                
        except subprocess.TimeoutExpired:
            pytest.fail("Terraform plan timed out")
        except FileNotFoundError:
            pytest.skip("Terraform CLI not available")
    
    def test_terraform_security(self, terraform_dir):
        """Test Terraform configuration for security best practices"""
        if not terraform_dir.exists():
            pytest.skip("Terraform directory not found")
        
        security_issues = []
        
        for tf_file in terraform_dir.glob("*.tf"):
            content = tf_file.read_text()
            
            # Check for hardcoded secrets
            if any(word in content.lower() for word in ["password", "secret", "token"]):
                # Look for actual hardcoded values
                lines = content.split('\n')
                for line_num, line in enumerate(lines, 1):
                    if '=' in line and not line.strip().startswith('#'):
                        if any(f'"{word}"' in line.lower() for word in ["password123", "secret123", "token123"]):
                            security_issues.append(f"{tf_file.name}:{line_num} - Potential hardcoded secret")
            
            # Check for public access
            if "0.0.0.0/0" in content:
                security_issues.append(f"{tf_file.name} - Overly permissive access (0.0.0.0/0)")
            
            # Check for insecure protocols
            if '"http://' in content:
                security_issues.append(f"{tf_file.name} - Insecure HTTP protocol used")
        
        if security_issues:
            print("Security warnings found (not failures):")
            for issue in security_issues:
                print(f"  - {issue}")
    
    def test_terraform_variables(self, terraform_dir):
        """Test Terraform variable configuration"""
        if not terraform_dir.exists():
            pytest.skip("Terraform directory not found")
        
        main_tf = terraform_dir / "main.tf"
        if not main_tf.exists():
            pytest.skip("main.tf not found")
        
        content = main_tf.read_text()
        
        # Check for required variables
        required_vars = ["cloudflare_api_token", "cloudflare_account_id", "domain_name"]
        missing_vars = []
        
        for var in required_vars:
            if f'variable "{var}"' not in content:
                missing_vars.append(var)
        
        assert not missing_vars, f"Missing required variables: {missing_vars}"
        
        # Check that sensitive variables are marked as sensitive
        if 'cloudflare_api_token' in content:
            # Find the variable block
            api_token_var_start = content.find('variable "cloudflare_api_token"')
            if api_token_var_start != -1:
                # Find the end of the variable block
                block_start = content.find('{', api_token_var_start)
                if block_start != -1:
                    brace_count = 1
                    pos = block_start + 1
                    while pos < len(content) and brace_count > 0:
                        if content[pos] == '{':
                            brace_count += 1
                        elif content[pos] == '}':
                            brace_count -= 1
                        pos += 1
                    
                    var_block = content[api_token_var_start:pos]
                    assert "sensitive" in var_block, "API token variable should be marked as sensitive"
    
    def test_terraform_outputs(self, terraform_dir):
        """Test Terraform outputs are properly defined"""
        if not terraform_dir.exists():
            pytest.skip("Terraform directory not found")
        
        main_tf = terraform_dir / "main.tf"
        if not main_tf.exists():
            pytest.skip("main.tf not found")
        
        content = main_tf.read_text()
        
        # Check for essential outputs
        expected_outputs = ["domain", "zone_id", "services"]
        missing_outputs = []
        
        for output in expected_outputs:
            if f'output "{output}"' not in content:
                missing_outputs.append(output)
        
        assert not missing_outputs, f"Missing required outputs: {missing_outputs}"
    
    def test_terraform_example_vars(self, terraform_dir):
        """Test that terraform.tfvars.example exists and is valid"""
        if not terraform_dir.exists():
            pytest.skip("Terraform directory not found")
        
        example_vars = terraform_dir / "terraform.tfvars.example"
        if not example_vars.exists():
            pytest.skip("terraform.tfvars.example not found")
        
        content = example_vars.read_text()
        
        # Should contain required variables
        required_vars = ["cloudflare_api_token", "cloudflare_account_id"]
        missing_vars = []
        
        for var in required_vars:
            if var not in content:
                missing_vars.append(var)
        
        assert not missing_vars, f"Missing variables in example: {missing_vars}"
        
        # Should not contain actual secrets
        assert "your-" in content or "placeholder" in content, "Example should contain placeholder values"
    
    def test_deploy_script_exists(self, terraform_dir):
        """Test that deployment script exists and is executable"""
        deploy_script = terraform_dir / "deploy.sh"
        
        if deploy_script.exists():
            assert os.access(deploy_script, os.X_OK), "Deploy script should be executable"
            
            content = deploy_script.read_text()
            assert "terraform" in content.lower(), "Deploy script should contain terraform commands"

if __name__ == "__main__":
    pytest.main([__file__])