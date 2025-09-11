#!/usr/bin/env python3
"""Test script to verify robust imports work in all environments."""

import os
import sys
from pathlib import Path


# Robust path setup that works in all environments (terminal, debugger, pytest)
def setup_python_path():
    """Ensure the project root is in Python path."""
    # First try to import test_utils (preferred method)
    try:
        import tests.utils.test_utils  # This sets up the Python path
        return
    except (ImportError, ModuleNotFoundError):
        pass
    
    # Fallback: manually find and add project root
    current_file = Path(__file__).resolve()
    
    # Look for project root by checking for marker files
    current_dir = current_file.parent
    max_levels = 5
    
    for _ in range(max_levels):
        # Look for specific marker files that indicate the PROJECT ROOT (not subdirs)
        # Must have BOTH a config file AND the rami package directory
        has_config = any((current_dir / marker).exists() for marker in ['pyproject.toml', 'requirements.txt', 'setup.py'])
        has_rami = (current_dir / 'rami').exists() and (current_dir / 'rami').is_dir()
        
        if has_config and has_rami:
            project_root = str(current_dir)
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
                print(f"✅ Added project root to path: {project_root}")
            return
        
        parent = current_dir.parent
        if parent == current_dir:  # Reached filesystem root
            break
        current_dir = parent
    
    # Last resort: relative path from current file
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        print(f"✅ Added project root to path (fallback): {project_root}")

# Set up the path
setup_python_path()

def test_imports():
    """Test that all imports work correctly."""
    print("🧪 Testing robust imports...")
    
    try:
        from gov.rami.rami_client import RamiClient
        print("✅ RamiClient imported successfully")
        
        # Test client creation
        client = RamiClient()
        print(f"✅ RamiClient created: {type(client).__name__}")
        
        # Test that it has expected methods
        methods = ['fetch_plans', 'download_plan_documents', 'download_multiple_plans_documents']
        for method in methods:
            if hasattr(client, method):
                print(f"✅ Method {method} exists")
            else:
                print(f"❌ Method {method} missing")
                return False
                
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def main():
    """Main test function."""
    print("🔧 Testing Robust Import System")
    print("=" * 50)
    
    print(f"🔍 Current working directory: {os.getcwd()}")
    print(f"🔍 Script location: {__file__}")
    print(f"🔍 Python path entries:")
    for i, path in enumerate(sys.path[:5]):  # Show first 5 entries
        print(f"   {i+1}. {path}")
    
    print("\n" + "=" * 50)
    
    success = test_imports()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All import tests passed!")
    else:
        print("❌ Import tests failed!")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
