# create_tables.py
"""
Utility script to create all SQLAlchemy tables defined in the project.
Run it before starting the FastAPI server:
    python backend/app/create_tables.py
"""

from app.database import engine, Base

def main():
    # Create all tables if they don't exist
    Base.metadata.create_all(bind=engine)
    print("All tables created (or already exist).")

if __name__ == "__main__":
    main()
