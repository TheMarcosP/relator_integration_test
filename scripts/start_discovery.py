#!/usr/bin/env python3
"""
Startup script for RelatorDiscovery server
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from discovery.server import main

if __name__ == "__main__":
    main() 