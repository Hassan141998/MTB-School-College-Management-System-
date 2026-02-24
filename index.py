import os
import sys

print("VERCEL BOOT: Checking environment variables...")
# Print out keys safely to see if DATABASE_URL is even being passed to the function
print("VERCEL ENV KEYS:", list(os.environ.keys()))
if 'DATABASE_URL' in os.environ:
    print("VERCEL DB URL FOUND (starts with):", os.environ['DATABASE_URL'][:15])
else:
    print("VERCEL CRTITICAL ERROR: DATABASE_URL is completely missing from os.environ")

# Ensure Vercel can find the app module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

# Vercel's python serverless function wrapper looks for 'app'
app = create_app(os.getenv('FLASK_CONFIG') or 'production')
