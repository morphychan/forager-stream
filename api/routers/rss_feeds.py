from typing import List, Optional, Set
from datetime import datetime
import re

from fastapi import APIRouter, Depends, HTTPException, Query, status, Path
from pydantic import BaseModel, HttpUrl, validator, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from api.deps import get_db
from src.forager.storage.models import RSSFeed, Category, Tag

# Pydantic schemas
class TagBase(BaseModel):
    """Base schema for tag data."""
    name: str = Field(..., description="Name of the tag", example="tech")

class TagCreate(TagBase):
    """Schema for creating a new tag."""
    pass

class TagInDB(TagBase):
    """Schema for tag data from database."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

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
    string_id: Optional[str] = Field(None, description="Unique string identifier for the feed (used in configs)", example="tech-news")
    category_id: int = Field(..., description="ID of the category this feed belongs to", example=1)
    tag_ids: Optional[List[int]] = Field(None, description="List of tag IDs to associate with this feed", example=[1, 2])
    tags: Optional[List[str]] = Field(None, description="List of tag names to associate with this feed", example=["tech", "news"])
    
    @validator('string_id')
    def validate_string_id(cls, v):
        """Validate that string_id contains only allowed characters."""
        if v is not None:
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError("string_id can only contain letters, numbers, underscores, and hyphens")
        return v

class FeedUpdate(BaseModel):
    """Schema for updating an existing feed."""
    name: Optional[str] = Field(None, description="Name of the RSS feed", example="Tech News")
    url: Optional[HttpUrl] = Field(None, description="URL of the RSS feed", example="https://news.example.com/rss")
    string_id: Optional[str] = Field(None, description="Unique string identifier for the feed", example="tech-news")
    poll_interval: Optional[int] = Field(None, description="Polling interval in seconds", example=3600)
    category_id: Optional[int] = Field(None, description="ID of the category this feed belongs to", example=1)
    status: Optional[str] = Field(None, description="Status of the feed", example="active")
    tag_ids: Optional[List[int]] = Field(None, description="List of tag IDs to associate with this feed", example=[1, 2])
    tags: Optional[List[str]] = Field(None, description="List of tag names to associate with this feed", example=["tech", "news"])
    
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
    
    @validator('string_id')
    def validate_string_id(cls, v):
        """Validate that string_id contains only allowed characters."""
        if v is not None:
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError("string_id can only contain letters, numbers, underscores, and hyphens")
        return v

class FeedInDB(FeedBase):
    """Schema for feed data from database."""
    id: int
    string_id: Optional[str] = None
    category_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    last_error: Optional[str] = None
    last_error_at: Optional[datetime] = None
    tags: List[TagInDB] = []
    
    class Config:
        from_attributes = True

class CategoryInDB(BaseModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class TagUpdate(BaseModel):
    """Schema for updating an existing tag."""
    name: str = Field(..., description="Updated name of the tag", example="technology")

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
    category = db.query(Category).filter(Category.id == feed.category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {feed.category_id} not found"
        )
    
    # Check if string_id already exists if provided
    if feed.string_id:
        existing_feed = db.query(RSSFeed).filter(
            RSSFeed.string_id == feed.string_id,
            RSSFeed.deleted_at.is_(None)
        ).first()
        if existing_feed:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Feed with string ID '{feed.string_id}' already exists"
            )
    
    # Process tags
    tags_to_associate = []
    
    # Process tag IDs if provided
    if feed.tag_ids:
        for tag_id in feed.tag_ids:
            tag = db.query(Tag).filter(Tag.id == tag_id).first()
            if not tag:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Tag with ID {tag_id} not found"
                )
            tags_to_associate.append(tag)
    
    # Process tag names if provided
    if feed.tags:
        for tag_name in feed.tags:
            # Check if tag exists, create if not
            tag = db.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.add(tag)
                try:
                    db.flush()  # Flush to get the ID without committing
                except SQLAlchemyError as e:
                    db.rollback()
                    print(f"[API] Error creating tag {tag_name}: {str(e)}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to create tag {tag_name}"
                    )
            tags_to_associate.append(tag)
    
    # Create new feed object
    db_feed = RSSFeed(
        string_id=feed.string_id,
        category_id=feed.category_id,
        name=feed.name,
        url=str(feed.url),  # Convert Pydantic HttpUrl to string
        poll_interval=feed.poll_interval,
        status="active"
    )
    
    # Associate tags
    db_feed.tags = tags_to_associate
    
    try:
        db.add(db_feed)
        db.commit()
        db.refresh(db_feed)
        print(f"[API] Created feed with ID: {db_feed.id}, string_id: {db_feed.string_id}")
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
def read_feed(feed_id: str = Path(..., description="The ID or string_id of the feed to retrieve"), db: Session = Depends(get_db)):
    """
    Retrieve a specific RSS feed by ID or string_id.
    
    Args:
        feed_id: ID or string_id of the feed to retrieve
        db: Database session dependency
        
    Returns:
        Feed object
        
    Raises:
        HTTPException: If feed not found
    """
    print(f"[API] Fetching feed with ID/string_id: {feed_id}")
    
    # Try to convert to integer (numeric ID)
    try:
        numeric_id = int(feed_id)
        feed = db.query(RSSFeed).filter(
            RSSFeed.id == numeric_id,
            RSSFeed.deleted_at.is_(None)
        ).first()
    except ValueError:
        # Use as string_id
        feed = db.query(RSSFeed).filter(
            RSSFeed.string_id == feed_id,
            RSSFeed.deleted_at.is_(None)
        ).first()
    
    if feed is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feed with ID/string_id {feed_id} not found"
        )
    
    return feed

@router.put("/{feed_id}", response_model=FeedInDB, summary="Update an RSS feed")
def update_feed(
    feed_update: FeedUpdate,
    feed_id: str = Path(..., description="The ID or string_id of the feed to update"),
    db: Session = Depends(get_db)
):
    """
    Update an existing RSS feed.
    
    Args:
        feed_update: Updated feed data
        feed_id: ID or string_id of the feed to update
        db: Database session dependency
        
    Returns:
        Updated feed object
        
    Raises:
        HTTPException: If feed not found or update fails
    """
    print(f"[API] Updating feed with ID/string_id {feed_id}: {feed_update.dict(exclude_unset=True)}")
    
    # Try to convert to integer (numeric ID)
    try:
        numeric_id = int(feed_id)
        feed = db.query(RSSFeed).filter(
            RSSFeed.id == numeric_id,
            RSSFeed.deleted_at.is_(None)
        ).first()
    except ValueError:
        # Use as string_id
        feed = db.query(RSSFeed).filter(
            RSSFeed.string_id == feed_id,
            RSSFeed.deleted_at.is_(None)
        ).first()
    
    if feed is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feed with ID/string_id {feed_id} not found"
        )
    
    # Check if category exists if changing it
    if feed_update.category_id is not None:
        category = db.query(Category).filter(Category.id == feed_update.category_id).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID {feed_update.category_id} not found"
            )
    
    # Check if string_id already exists if provided
    if feed_update.string_id is not None and feed_update.string_id != feed.string_id:
        existing_feed = db.query(RSSFeed).filter(
            RSSFeed.string_id == feed_update.string_id,
            RSSFeed.deleted_at.is_(None),
            RSSFeed.id != feed.id
        ).first()
        if existing_feed:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Feed with string ID '{feed_update.string_id}' already exists"
            )
    
    # Process tags if provided
    if feed_update.tag_ids is not None or feed_update.tags is not None:
        tags_to_associate = []
        
        # Process tag IDs if provided
        if feed_update.tag_ids is not None:
            for tag_id in feed_update.tag_ids:
                tag = db.query(Tag).filter(Tag.id == tag_id).first()
                if not tag:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Tag with ID {tag_id} not found"
                    )
                tags_to_associate.append(tag)
        
        # Process tag names if provided
        if feed_update.tags is not None:
            for tag_name in feed_update.tags:
                # Check if tag exists, create if not
                tag = db.query(Tag).filter(Tag.name == tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.add(tag)
                    try:
                        db.flush()  # Flush to get the ID without committing
                    except SQLAlchemyError as e:
                        db.rollback()
                        print(f"[API] Error creating tag {tag_name}: {str(e)}")
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to create tag {tag_name}"
                        )
                tags_to_associate.append(tag)
        
        # Replace existing tags
        feed.tags = tags_to_associate
    
    # Update feed attributes
    update_data = feed_update.dict(exclude_unset=True, exclude={"tag_ids", "tags"})
    if 'url' in update_data:
        update_data['url'] = str(update_data['url'])  # Convert Pydantic HttpUrl to string
    
    for key, value in update_data.items():
        setattr(feed, key, value)
    
    try:
        db.commit()
        db.refresh(feed)
        print(f"[API] Successfully updated feed with ID: {feed.id}, string_id: {feed.string_id}")
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
    feed_id: str = Path(..., description="The ID or string_id of the feed to delete"),
    hard_delete: bool = Query(False, description="Whether to permanently delete the feed"),
    db: Session = Depends(get_db)
):
    """
    Delete an RSS feed.
    
    Args:
        feed_id: ID or string_id of the feed to delete
        hard_delete: If True, permanently delete; if False, soft delete
        db: Database session dependency
        
    Returns:
        No content
        
    Raises:
        HTTPException: If feed not found or deletion fails
    """
    print(f"[API] Deleting feed with ID/string_id {feed_id} (hard_delete={hard_delete})")
    
    # Try to convert to integer (numeric ID)
    try:
        numeric_id = int(feed_id)
        feed = db.query(RSSFeed).filter(
            RSSFeed.id == numeric_id,
            RSSFeed.deleted_at.is_(None) if not hard_delete else True
        ).first()
    except ValueError:
        # Use as string_id
        feed = db.query(RSSFeed).filter(
            RSSFeed.string_id == feed_id,
            RSSFeed.deleted_at.is_(None) if not hard_delete else True
        ).first()
    
    if feed is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feed with ID/string_id {feed_id} not found"
        )
    
    try:
        if hard_delete:
            db.delete(feed)
        else:
            feed.deleted_at = datetime.utcnow()
        
        db.commit()
        print(f"[API] Successfully deleted feed with ID/string_id: {feed_id}")
        return None
    except SQLAlchemyError as e:
        db.rollback()
        print(f"[API] Error deleting feed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete feed"
        )

@router.get("/categories/", response_model=List[CategoryInDB], summary="List all categories")
def list_categories(db: Session = Depends(get_db)):
    """
    Get all feed categories.
    """
    categories = db.query(Category).order_by(Category.id).all()
    return categories

@router.get("/tags/", response_model=List[TagInDB], summary="List all tags")
def list_tags(db: Session = Depends(get_db)):
    """
    Get all tags.
    """
    tags = db.query(Tag).order_by(Tag.name).all()
    return tags

@router.post("/tags/", response_model=TagInDB, status_code=status.HTTP_201_CREATED, summary="Create a new tag")
def create_tag(tag: TagCreate, db: Session = Depends(get_db)):
    """
    Create a new tag.
    
    Args:
        tag: Tag data
        db: Database session dependency
        
    Returns:
        Created tag object
        
    Raises:
        HTTPException: If tag creation fails
    """
    print(f"[API] Creating new tag: {tag.dict()}")
    
    # Check if tag already exists
    existing_tag = db.query(Tag).filter(Tag.name == tag.name).first()
    if existing_tag:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tag with name '{tag.name}' already exists"
        )
    
    # Create new tag
    db_tag = Tag(
        name=tag.name
    )
    
    try:
        db.add(db_tag)
        db.commit()
        db.refresh(db_tag)
        print(f"[API] Created tag with ID: {db_tag.id}")
        return db_tag
    except SQLAlchemyError as e:
        db.rollback()
        print(f"[API] Error creating tag: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create tag"
        )

@router.post("/{feed_id}/tags/{tag_id}", response_model=FeedInDB, summary="Add a tag to a feed")
def add_tag_to_feed(
    feed_id: str = Path(..., description="The ID or string_id of the feed"),
    tag_id: int = Path(..., description="The ID of the tag to add"),
    db: Session = Depends(get_db)
):
    """
    Add a tag to a feed.
    
    Args:
        feed_id: ID or string_id of the feed
        tag_id: ID of the tag to add
        db: Database session dependency
        
    Returns:
        Updated feed object
        
    Raises:
        HTTPException: If feed or tag not found, or operation fails
    """
    print(f"[API] Adding tag {tag_id} to feed {feed_id}")
    
    # Try to convert to integer (numeric ID)
    try:
        numeric_id = int(feed_id)
        feed = db.query(RSSFeed).filter(
            RSSFeed.id == numeric_id,
            RSSFeed.deleted_at.is_(None)
        ).first()
    except ValueError:
        # Use as string_id
        feed = db.query(RSSFeed).filter(
            RSSFeed.string_id == feed_id,
            RSSFeed.deleted_at.is_(None)
        ).first()
    
    if feed is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feed with ID/string_id {feed_id} not found"
        )
    
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if tag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with ID {tag_id} not found"
        )
    
    # Check if tag is already associated with feed
    if tag in feed.tags:
        return feed  # Tag already associated, return feed as is
    
    # Add tag to feed
    feed.tags.append(tag)
    
    try:
        db.commit()
        db.refresh(feed)
        print(f"[API] Successfully added tag {tag_id} to feed {feed_id}")
        return feed
    except SQLAlchemyError as e:
        db.rollback()
        print(f"[API] Error adding tag to feed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add tag to feed"
        )

@router.delete("/{feed_id}/tags/{tag_id}", response_model=FeedInDB, summary="Remove a tag from a feed")
def remove_tag_from_feed(
    feed_id: str = Path(..., description="The ID or string_id of the feed"),
    tag_id: int = Path(..., description="The ID of the tag to remove"),
    db: Session = Depends(get_db)
):
    """
    Remove a tag from a feed.
    
    Args:
        feed_id: ID or string_id of the feed
        tag_id: ID of the tag to remove
        db: Database session dependency
        
    Returns:
        Updated feed object
        
    Raises:
        HTTPException: If feed or tag not found, or operation fails
    """
    print(f"[API] Removing tag {tag_id} from feed {feed_id}")
    
    # Try to convert to integer (numeric ID)
    try:
        numeric_id = int(feed_id)
        feed = db.query(RSSFeed).filter(
            RSSFeed.id == numeric_id,
            RSSFeed.deleted_at.is_(None)
        ).first()
    except ValueError:
        # Use as string_id
        feed = db.query(RSSFeed).filter(
            RSSFeed.string_id == feed_id,
            RSSFeed.deleted_at.is_(None)
        ).first()
    
    if feed is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feed with ID/string_id {feed_id} not found"
        )
    
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if tag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with ID {tag_id} not found"
        )
    
    # Check if tag is associated with feed
    if tag not in feed.tags:
        return feed  # Tag not associated, return feed as is
    
    # Remove tag from feed
    feed.tags.remove(tag)
    
    try:
        db.commit()
        db.refresh(feed)
        print(f"[API] Successfully removed tag {tag_id} from feed {feed_id}")
        return feed
    except SQLAlchemyError as e:
        db.rollback()
        print(f"[API] Error removing tag from feed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove tag from feed"
        )

@router.put("/tags/{tag_id}", response_model=TagInDB, summary="Update a tag")
def update_tag(
    tag_id: int = Path(..., description="ID of the tag to update"),
    tag_update: TagUpdate = ...,
    db: Session = Depends(get_db)
):
    """
    Update an existing tag.
    
    Args:
        tag_id: ID of the tag to update
        tag_update: Updated tag data
        db: Database session dependency
        
    Returns:
        Updated tag object
        
    Raises:
        HTTPException: If tag not found or update fails
    """
    print(f"[API] Updating tag with ID {tag_id}: {tag_update.dict()}")
    
    # Find the tag
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with ID {tag_id} not found"
        )
    
    # Check if new name already exists (for another tag)
    existing_tag = db.query(Tag).filter(
        Tag.name == tag_update.name,
        Tag.id != tag_id
    ).first()
    if existing_tag:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tag with name '{tag_update.name}' already exists"
        )
    
    # Update tag
    tag.name = tag_update.name
    
    try:
        db.commit()
        db.refresh(tag)
        print(f"[API] Successfully updated tag {tag_id}")
        return tag
    except SQLAlchemyError as e:
        db.rollback()
        print(f"[API] Error updating tag: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update tag"
        )

@router.delete("/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a tag")
def delete_tag(
    tag_id: int = Path(..., description="ID of the tag to delete"),
    db: Session = Depends(get_db)
):
    """
    Delete a tag. This will also remove all associations with feeds and articles.
    
    Args:
        tag_id: ID of the tag to delete
        db: Database session dependency
        
    Returns:
        No content
        
    Raises:
        HTTPException: If tag not found or deletion fails
    """
    print(f"[API] Deleting tag with ID {tag_id}")
    
    # Find the tag
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with ID {tag_id} not found"
        )
    
    try:
        db.delete(tag)
        db.commit()
        print(f"[API] Successfully deleted tag {tag_id}")
        return None
    except SQLAlchemyError as e:
        db.rollback()
        print(f"[API] Error deleting tag: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete tag"
        )
