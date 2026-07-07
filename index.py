import os
import sys

if 'DATABASE_URL' in os.environ:
    print("VERCEL BOOT: DATABASE_URL is set.")
else:
    print("VERCEL BOOT WARNING: DATABASE_URL is missing — the app will fall "
          "back to an empty, non-persistent SQLite database.")

# Ensure Vercel can find the app module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

# Vercel's python serverless function wrapper looks for 'app'
app = create_app(os.getenv('FLASK_CONFIG') or 'production')
