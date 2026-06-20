# backend/app/dependencies.py
# Simple wrapper to expose DB session dependency for FastAPI routes.
# Delegates to the get_db generator defined in database.py.

from .database import get_db
