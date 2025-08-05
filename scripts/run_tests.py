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
    print("[*] TableTalk Test Runner")
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
    
    # Get Python executable
    python_exe = sys.executable
    
    print(f"[*] Project root: {project_root}")
    print(f"[*] Python executable: {python_exe}")
    print()
    
    # Build test command
    cmd = [python_exe, "-m", "pytest", "tests/", "-v"]
    print(f"[>] Running: {' '.join(cmd)}")
    
    try:
        # Run tests
        result = subprocess.run(cmd, cwd=project_root)
        
        if result.returncode == 0:
            print("\n[+] All tests passed!")
        else:
            print(f"\n[-] Tests failed with exit code {result.returncode}")
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"[-] Error running tests: {e}")
        return False


if __name__ == "__main__":
    sys.exit(main())
