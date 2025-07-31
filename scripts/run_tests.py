#!/usr/bin/env python3
"""
TableTalk Test Runner

Simple script to run the end-to-end tests.
"""

import os
import sys
import subprocess
from pathlib import Path


def main():
    """Run TableTalk tests."""
    print("🧪 TableTalk Test Runner")
    print("=" * 40)
    
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Change to project directory
    os.chdir(str(project_root))
    
    # Set up environment
    src_path = project_root / "src"
    env = os.environ.copy()
    env['PYTHONPATH'] = str(src_path)
    
    print(f"📁 Project root: {project_root}")
    print(f"🐍 Python path: {src_path}")
    
    # Run tests
    cmd = [sys.executable, "-m", "pytest", "tests/test_end_to_end.py", "-v"]
    
    print(f"🚀 Running: {' '.join(cmd)}")
    print("=" * 40)
    
    try:
        result = subprocess.run(cmd, env=env, check=False)
        
        if result.returncode == 0:
            print("\n🎉 All tests passed!")
        else:
            print(f"\n❌ Tests failed with exit code {result.returncode}")
            
        return result.returncode
        
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
