#!/usr/bin/env python3
"""
TableTalk entry point script.

This script provides the main entry point for running TableTalk.
It properly sets up the Python path and imports from the src package.
"""

import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Import and run main
from src.main import main

if __name__ == "__main__":
    main()
