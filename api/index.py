import os
import sys

# Ensure backend directory is in Python path for Vercel Serverless Runtime
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from main import app

# Vercel Serverless handler
handler = app
