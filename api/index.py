import os
import sys

# Compute absolute directory path of Vercel serverless environment
dir_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(dir_path, ".."))

if root_path not in sys.path:
    sys.path.insert(0, root_path)

backend_path = os.path.join(root_path, "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Import the main Flask application
from backend.app import app
