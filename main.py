"""
AuroSys Command Center - Hackathon Edition (v9.5)
-------------------------------------------------
Refactored into `aurosys` package.
"""

import sys
import os

# Ensure current directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui_app import render_app

if __name__ == "__main__":
    render_app()