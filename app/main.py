# Shim so tests like `from app.main import app` work.
# Re-export the FastAPI instance from your backend package.
from backend.app.api.app import app  # adjust this import if your FastAPI object lives elsewhere
