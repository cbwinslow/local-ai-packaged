#!/usr/bin/env python3
"""
Test Runner for Local AI Package
Runs comprehensive tests with proper categorization and reporting
"""

import sys
import subprocess
import argparse
from pathlib import Path
import time

def run_command(cmd, description, timeout=300):
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(cmd, timeout=timeout, check=False)
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ {description} completed successfully ({elapsed:.1f}s)")
            return True
        else:
            print(f"❌ {description} failed with exit code {result.returncode} ({elapsed:.1f}s)")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} timed out after {timeout}s")
        return False
    except KeyboardInterrupt:
        print(f"🛑 {description} interrupted by user")
        return False

def main():
    parser = argparse.ArgumentParser(description="Run Local AI Package tests")
    parser.add_argument("--category", choices=[
        "all", "unit", "integration", "security", "docker", "terraform", "smoke"
    ], default="all", help="Test category to run")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--fast", "-f", action="store_true", help="Skip slow tests")
    parser.add_argument("--parallel", "-p", action="store_true", help="Run tests in parallel")
    parser.add_argument("--coverage", "-c", action="store_true", help="Generate coverage report")
    parser.add_argument("--html-report", action="store_true", help="Generate HTML report")
    
    args = parser.parse_args()
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add verbosity
    if args.verbose:
        cmd.append("-vv")
    else:
        cmd.append("-v")
    
    # Add category filters
    if args.category != "all":
        cmd.extend(["-m", args.category])
    
    # Skip slow tests if requested
    if args.fast:
        if args.category == "all":
            cmd.extend(["-m", "not slow"])
        else:
            cmd.extend(["-m", f"{args.category} and not slow"])
    
    # Add parallel execution
    if args.parallel:
        try:
            import pytest_xdist
            cmd.extend(["-n", "auto"])
        except ImportError:
            print("⚠️  pytest-xdist not installed, running tests sequentially")
    
    # Add coverage
    if args.coverage:
        cmd.extend([
            "--cov=.",
            "--cov-report=term-missing",
            "--cov-report=xml:reports/coverage.xml"
        ])
    
    # Add HTML report
    if args.html_report:
        cmd.extend([
            "--html=reports/pytest-report.html",
            "--self-contained-html"
        ])
    
    # Ensure reports directory exists
    Path("reports").mkdir(exist_ok=True)
    
    # Run tests
    print(f"🚀 Starting Local AI Package tests (category: {args.category})")
    
    success = run_command(cmd, f"{args.category.title()} Tests", timeout=600)
    
    if success:
        print(f"\n🎉 All {args.category} tests completed successfully!")
        return 0
    else:
        print(f"\n💥 Some {args.category} tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())