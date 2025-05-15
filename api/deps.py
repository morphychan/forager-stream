from typing import Generator
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

# Import SessionLocal from the database configuration
from src.forager.storage.base import SessionLocal

def get_db() -> Generator[Session, None, None]:
    """
    Create a new SQLAlchemy Session per request, and close it after.
    
    This dependency function manages the database session lifecycle:
    1. Creates a new session from the configured SessionLocal factory
    2. Yields the session to the route function
    3. Commits changes if no exceptions occur
    4. Rolls back changes if an exception occurs
    5. Always closes the session to return it to the connection pool
    
    Yields:
        Session: A SQLAlchemy database session.
        
    Raises:
        HTTPException: When a database error occurs.
    """
    print("[DB] Creating new database session")
    db = SessionLocal()
    try:
        print("[DB] Yielding database session to route handler")
        yield db
        print("[DB] Route handler completed, committing transaction")
        db.commit()
    except Exception as e:
        print(f"[DB] Error during request: {str(e)}")
        db.rollback()
        # Print the specific exception type and details
        print(f"Database error: {str(e)}")
        # Re-raise as HTTP exception for proper API error response
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database operation failed. Please try again later."
        ) from e
    finally:
        print("[DB] Closing database session")
        db.close()

# Note: To configure database connection pool parameters,
# modify SessionLocal creation in src/forager/storage/base.py with:
#
# engine = create_engine(
#     SQLALCHEMY_DATABASE_URL,
#     pool_size=20,                 # Maximum number of connections to keep
#     max_overflow=10,              # Maximum number of connections to create beyond pool_size
#     pool_timeout=30,              # Seconds to wait before timeout on connection pool checkout
#     pool_recycle=1800,            # Seconds after which a connection is recycled
#     pool_pre_ping=True            # Enable connection health checks
# )
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
