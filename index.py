import os
import sys

# Ensure Vercel can find the app module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

# Vercel's python serverless function wrapper looks for 'app'
app = create_app(os.getenv('FLASK_CONFIG') or 'production')
