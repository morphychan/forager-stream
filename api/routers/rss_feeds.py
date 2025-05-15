from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status, Path
from pydantic import BaseModel, HttpUrl, validator, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from api.deps import get_db
from src.forager.storage.models import RSSFeed

# Pydantic schemas
class FeedBase(BaseModel):
    """Base Pydantic schema with common feed attributes."""
    name: str = Field(..., description="Name of the RSS feed", example="Tech News")
    url: HttpUrl = Field(..., description="URL of the RSS feed", example="https://news.example.com/rss")
    poll_interval: int = Field(3600, description="Polling interval in seconds", example=3600)
    
    @validator('poll_interval')
    def validate_poll_interval(cls, v):
        """Validate polling interval is reasonable."""
        if v < 60:
            raise ValueError('Poll interval must be at least 60 seconds')
        return v

class FeedCreate(FeedBase):
    """Schema for creating a new feed."""
    category_id: int = Field(..., description="ID of the category this feed belongs to", example=1)

class FeedUpdate(BaseModel):
    """Schema for updating an existing feed."""
    name: Optional[str] = Field(None, description="Name of the RSS feed", example="Tech News")
    url: Optional[HttpUrl] = Field(None, description="URL of the RSS feed", example="https://news.example.com/rss")
    poll_interval: Optional[int] = Field(None, description="Polling interval in seconds", example=3600)
    category_id: Optional[int] = Field(None, description="ID of the category this feed belongs to", example=1)
    status: Optional[str] = Field(None, description="Status of the feed", example="active")
    
    @validator('poll_interval')
    def validate_poll_interval(cls, v):
        if v is not None and v < 60:
            raise ValueError('Poll interval must be at least 60 seconds')
        return v
    
    @validator('status')
    def validate_status(cls, v):
        if v is not None and v not in ['active', 'paused', 'error']:
            raise ValueError('Status must be one of: active, paused, error')
        return v

class FeedInDB(FeedBase):
    """Schema for feed data from database."""
    id: int
    category_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    last_error: Optional[str] = None
    last_error_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

# Router
router = APIRouter()

@router.get("/", response_model=List[FeedInDB], summary="List RSS feeds")
def read_feeds(
    db: Session = Depends(get_db),
    skip: int = Query(0, description="Number of items to skip for pagination"),
    limit: int = Query(100, description="Maximum number of items to return"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    status: Optional[str] = Query(None, description="Filter by feed status")
):
    """
    Retrieve RSS feeds with pagination and filtering options.
    
    Args:
        db: Database session dependency
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        category_id: Optional filter by category
        status: Optional filter by status
        
    Returns:
        List of RSS feed objects
    """
    print(f"[API] Fetching feeds with skip={skip}, limit={limit}, category_id={category_id}, status={status}")
    
    # Create query
    query = db.query(RSSFeed)
    
    # Apply filters
    if category_id is not None:
        query = query.filter(RSSFeed.category_id == category_id)
    if status is not None:
        query = query.filter(RSSFeed.status == status)
    
    # Filter out deleted feeds
    query = query.filter(RSSFeed.deleted_at.is_(None))
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    # Execute query
    feeds = query.all()
    
    print(f"[API] Found {len(feeds)} feeds")
    return feeds

@router.post("/", response_model=FeedInDB, status_code=status.HTTP_201_CREATED, summary="Create a new RSS feed")
def create_feed(feed: FeedCreate, db: Session = Depends(get_db)):
    """
    Create a new RSS feed.
    
    Args:
        feed: Feed data
        db: Database session dependency
        
    Returns:
        Created feed object
        
    Raises:
        HTTPException: If feed creation fails
    """
    print(f"[API] Creating new feed: {feed.dict()}")
    
    # Check if category exists
    from src.forager.storage.models import Category
    category = db.query(Category).filter(Category.id == feed.category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {feed.category_id} not found"
        )
    
    # Create new feed object
    db_feed = RSSFeed(
        category_id=feed.category_id,
        name=feed.name,
        url=str(feed.url),  # Convert Pydantic HttpUrl to string
        poll_interval=feed.poll_interval,
        status="active"
    )
    
    try:
        db.add(db_feed)
        db.commit()
        db.refresh(db_feed)
        print(f"[API] Created feed with ID: {db_feed.id}")
        return db_feed
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Feed with this URL already exists"
        )
    except SQLAlchemyError as e:
        db.rollback()
        print(f"[API] Error creating feed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create feed"
        )

@router.get("/{feed_id}", response_model=FeedInDB, summary="Get a specific RSS feed")
def read_feed(feed_id: int = Path(..., description="The ID of the feed to retrieve"), db: Session = Depends(get_db)):
    """
    Retrieve a specific RSS feed by ID.
    
    Args:
        feed_id: ID of the feed to retrieve
        db: Database session dependency
        
    Returns:
        Feed object
        
    Raises:
        HTTPException: If feed not found
    """
    print(f"[API] Fetching feed with ID: {feed_id}")
    
    feed = db.query(RSSFeed).filter(
        RSSFeed.id == feed_id,
        RSSFeed.deleted_at.is_(None)
    ).first()
    
    if feed is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feed with ID {feed_id} not found"
        )
    
    return feed

@router.put("/{feed_id}", response_model=FeedInDB, summary="Update an RSS feed")
def update_feed(
    feed_update: FeedUpdate,
    feed_id: int = Path(..., description="The ID of the feed to update"),
    db: Session = Depends(get_db)
):
    """
    Update an existing RSS feed.
    
    Args:
        feed_update: Updated feed data
        feed_id: ID of the feed to update
        db: Database session dependency
        
    Returns:
        Updated feed object
        
    Raises:
        HTTPException: If feed not found or update fails
    """
    print(f"[API] Updating feed with ID {feed_id}: {feed_update.dict(exclude_unset=True)}")
    
    # Get existing feed
    feed = db.query(RSSFeed).filter(
        RSSFeed.id == feed_id,
        RSSFeed.deleted_at.is_(None)
    ).first()
    
    if feed is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feed with ID {feed_id} not found"
        )
    
    # Check if category exists if changing it
    if feed_update.category_id is not None:
        from src.forager.storage.models import Category
        category = db.query(Category).filter(Category.id == feed_update.category_id).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID {feed_update.category_id} not found"
            )
    
    # Update feed attributes
    update_data = feed_update.dict(exclude_unset=True)
    if 'url' in update_data:
        update_data['url'] = str(update_data['url'])  # Convert Pydantic HttpUrl to string
    
    for key, value in update_data.items():
        setattr(feed, key, value)
    
    try:
        db.commit()
        db.refresh(feed)
        print(f"[API] Successfully updated feed with ID: {feed_id}")
        return feed
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Feed with this URL already exists"
        )
    except SQLAlchemyError as e:
        db.rollback()
        print(f"[API] Error updating feed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update feed"
        )

@router.delete("/{feed_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete an RSS feed")
def delete_feed(
    feed_id: int = Path(..., description="The ID of the feed to delete"),
    hard_delete: bool = Query(False, description="Whether to permanently delete the feed"),
    db: Session = Depends(get_db)
):
    """
    Delete an RSS feed.
    
    Args:
        feed_id: ID of the feed to delete
        hard_delete: If True, permanently delete; if False, soft delete
        db: Database session dependency
        
    Returns:
        No content
        
    Raises:
        HTTPException: If feed not found or deletion fails
    """
    print(f"[API] Deleting feed with ID {feed_id} (hard_delete={hard_delete})")
    
    # Get existing feed
    feed = db.query(RSSFeed).filter(
        RSSFeed.id == feed_id,
        RSSFeed.deleted_at.is_(None) if not hard_delete else True
    ).first()
    
    if feed is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feed with ID {feed_id} not found"
        )
    
    try:
        if hard_delete:
            db.delete(feed)
        else:
            feed.deleted_at = datetime.utcnow()
        
        db.commit()
        print(f"[API] Successfully deleted feed with ID: {feed_id}")
        return None
    except SQLAlchemyError as e:
        db.rollback()
        print(f"[API] Error deleting feed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete feed"
        )
