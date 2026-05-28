"""
Vercel Serverless Entry Point
==============================
Wraps the Flask app for Vercel's serverless Python runtime.
"""

import sys
import os

# Add parent directory to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Vercel looks for an `app` variable in this module
