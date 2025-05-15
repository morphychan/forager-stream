"""
SQLAlchemy database configuration for the Forager application.

This module sets up the SQLAlchemy engine and session factory.
"""

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Get database URL from environment variable, or use a default SQLite database path
BASE_DIR = Path(__file__).resolve().parents[3]
default_db_path = BASE_DIR / "data" / "forager.db"
DATABASE_URL = os.environ.get(
    "DATABASE_URL", 
    f"sqlite:///{default_db_path}"
)

print(f"[DATABASE] Initializing database connection with URL: {DATABASE_URL}")

# Create SQLAlchemy engine with connection pool settings
engine = create_engine(
    DATABASE_URL,
    pool_size=20,                 # Maximum number of connections to keep
    max_overflow=10,              # Maximum number of connections to create beyond pool_size
    pool_timeout=30,              # Seconds to wait before timeout on connection pool checkout
    pool_recycle=1800,            # Seconds after which a connection is recycled
    pool_pre_ping=True,           # Enable connection health checks
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

print(f"[DATABASE] SQLAlchemy engine created with pool_size={20}, max_overflow={10}")

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

print("[DATABASE] SessionLocal factory initialized")

# Import models
from src.forager.storage.models import Base

print("[DATABASE] ORM models imported successfully") 