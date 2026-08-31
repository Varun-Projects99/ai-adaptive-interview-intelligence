import os
import sys

# Compute base repository paths dynamically
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))

# Import the existing Flask app object from backend/app.py
from backend.app import app
