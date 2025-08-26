# Shim so tests that do `from app.main import app` work.
# Re-export the actual FastAPI instance from your backend package.
from backend.app.api.app import app  # adjust if your FastAPI object lives elsewhere
