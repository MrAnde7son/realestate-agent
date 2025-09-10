#!/usr/bin/env python3
"""
Python Services Validation Script
Checks for common issues in Python services across the monorepo
"""

import os
import sys
import ast
import subprocess
from pathlib import Path
from typing import List, Dict, Set

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def find_python_files(directory: Path) -> List[Path]:
    """Find all Python files in directory."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Skip __pycache__ and .git directories
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules', 'venv']]
        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)
    return python_files

def check_imports(file_path: Path) -> List[str]:
    """Check for common import issues."""
    issues = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse AST
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith('.'):
                        # Check for relative imports that might be problematic
                        if len(alias.name.split('.')) > 3:
                            issues.append(f"Deep relative import: {alias.name}")
            
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith('.'):
                    # Check for relative imports
                    if len(node.module.split('.')) > 3:
                        issues.append(f"Deep relative import: {node.module}")
    
    except Exception as e:
        issues.append(f"Error parsing file: {e}")
    
    return issues

def check_requirements_files() -> List[str]:
    """Check for missing or inconsistent requirements files."""
    issues = []
    
    # Check for requirements.txt in each service
    services = ['backend-django', 'yad2', 'gov', 'mavat', 'rami', 'gis', 'orchestration', 'db', 'utils']
    
    for service in services:
        service_path = project_root / service
        if service_path.exists():
            req_file = service_path / 'requirements.txt'
            if not req_file.exists():
                issues.append(f"Missing requirements.txt in {service}")
            else:
                # Check if requirements.txt is empty
                if req_file.stat().st_size == 0:
                    issues.append(f"Empty requirements.txt in {service}")
    
    return issues

def check_django_models() -> List[str]:
    """Check Django models for common issues."""
    issues = []
    
    models_file = project_root / 'backend-django' / 'core' / 'models.py'
    if models_file.exists():
        try:
            with open(models_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for missing __str__ methods
            if 'class ' in content and '__str__' not in content:
                issues.append("Some models might be missing __str__ methods")
            
            # Check for missing Meta classes
            if 'class ' in content and 'class Meta:' not in content:
                issues.append("Some models might be missing Meta classes")
        
        except Exception as e:
            issues.append(f"Error checking Django models: {e}")
    
    return issues

def check_migrations() -> List[str]:
    """Check for migration issues."""
    issues = []
    
    migrations_dir = project_root / 'backend-django' / 'core' / 'migrations'
    if migrations_dir.exists():
        migration_files = list(migrations_dir.glob('*.py'))
        if not migration_files:
            issues.append("No migration files found")
        else:
            # Check for migration naming consistency
            for migration_file in migration_files:
                if not migration_file.name[0].isdigit():
                    issues.append(f"Migration file should start with number: {migration_file.name}")
    
    return issues

def check_test_coverage() -> List[str]:
    """Check test coverage."""
    issues = []
    
    # Check if tests directory exists
    tests_dir = project_root / 'tests'
    if not tests_dir.exists():
        issues.append("No tests directory found")
    else:
        # Check for test files
        test_files = list(tests_dir.glob('test_*.py'))
        if not test_files:
            issues.append("No test files found")
    
    return issues

def run_python_linting() -> List[str]:
    """Run Python linting checks."""
    issues = []
    
    try:
        # Check if flake8 is available
        result = subprocess.run(['flake8', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            issues.append("flake8 not available - install with: pip install flake8")
            return issues
        
        # Run flake8 on Python files
        python_files = find_python_files(project_root)
        for file_path in python_files:
            result = subprocess.run(['flake8', str(file_path)], capture_output=True, text=True)
            if result.returncode != 0:
                issues.append(f"Linting issues in {file_path}: {result.stdout}")
    
    except FileNotFoundError:
        issues.append("flake8 not found - install with: pip install flake8")
    
    return issues

def validate_python_services():
    """Main validation function."""
    print("🔍 Validating Python services...")
    
    all_issues = []
    
    # Check imports
    print("Checking imports...")
    python_files = find_python_files(project_root)
    for file_path in python_files:
        issues = check_imports(file_path)
        if issues:
            all_issues.extend([f"{file_path}: {issue}" for issue in issues])
    
    # Check requirements files
    print("Checking requirements files...")
    all_issues.extend(check_requirements_files())
    
    # Check Django models
    print("Checking Django models...")
    all_issues.extend(check_django_models())
    
    # Check migrations
    print("Checking migrations...")
    all_issues.extend(check_migrations())
    
    # Check test coverage
    print("Checking test coverage...")
    all_issues.extend(check_test_coverage())
    
    # Run linting
    print("Running Python linting...")
    all_issues.extend(run_python_linting())
    
    if all_issues:
        print("❌ Issues found:")
        for issue in all_issues:
            print(f"  - {issue}")
        return False
    else:
        print("✅ All Python services validation passed")
        return True

if __name__ == "__main__":
    success = validate_python_services()
    sys.exit(0 if success else 1)
