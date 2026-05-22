import os
import sys
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the app
from app import app, db

# This is the WSGI application that Vercel will use
# Export as 'app' for Vercel's Python runtime
@app.before_request
def ensure_uploads_folder():
    """Ensure uploads folder exists"""
    uploads_path = os.path.join(app.root_path, 'static', 'uploads')
    os.makedirs(uploads_path, exist_ok=True)

# Initialize database tables on startup
with app.app_context():
    db.create_all()
