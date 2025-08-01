import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# This file is now self-contained. It prepares the database tools.

# Correctly locate the project's root directory
# Correctly locate the project's root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATABASE_NAME = "billing_app.db"
DATABASE_PATH = os.path.join(PROJECT_ROOT, DATABASE_NAME)


# Setup the database engine
engine = create_engine(f'sqlite:///{DATABASE_PATH}')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create the Base class that all models will inherit from
Base = declarative_base()