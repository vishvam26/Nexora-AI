import os
import sys

# Ensure current apps/backend directory is on python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app

__all__ = ["app"]
