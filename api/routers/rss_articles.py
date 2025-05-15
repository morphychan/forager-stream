"""
API routes for RSS articles.
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status, Path
from pydantic import BaseModel, HttpUrl, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from api.deps import get_db
from src.forager.storage.models import RSSArticle, RSSFeed

# Pydantic models
class ArticleBase(BaseModel):
    """Base model for article data."""
    title: str = Field(..., description="Article title")
    link: HttpUrl = Field(..., description="URL to the full article")
    published_at: datetime = Field(..., description="Publication timestamp")
    
class ArticleInDB(ArticleBase):
    """Model for article data from database."""
    id: int
    feed_id: int
    fetched_at: datetime
    updated_at: datetime
    status: str
    summary: Optional[str] = None
    content: Optional[str] = None
    
    class Config:
        from_attributes = True

# Router
router = APIRouter()

@router.get("/", response_model=List[ArticleInDB], summary="List RSS articles")
def list_articles(
    db: Session = Depends(get_db),
    skip: int = Query(0, description="Number of items to skip for pagination"),
    limit: int = Query(100, description="Maximum number of items to return"),
    feed_id: Optional[int] = Query(None, description="Filter by feed ID"),
    status: Optional[str] = Query(None, description="Filter by article status"),
    before_date: Optional[datetime] = Query(None, description="Filter articles published before this date"),
    after_date: Optional[datetime] = Query(None, description="Filter articles published after this date")
):
    """
    Retrieve RSS articles with pagination and filtering options.
    """
    print(f"[API] Fetching articles with skip={skip}, limit={limit}, feed_id={feed_id}, status={status}")
    
    # Create base query
    query = db.query(RSSArticle)
    
    # Apply filters
    if feed_id is not None:
        query = query.filter(RSSArticle.feed_id == feed_id)
    if status is not None:
        query = query.filter(RSSArticle.status == status)
    if before_date is not None:
        query = query.filter(RSSArticle.published_at <= before_date)
    if after_date is not None:
        query = query.filter(RSSArticle.published_at >= after_date)
    
    # Only include non-deleted articles
    query = query.filter(RSSArticle.deleted_at.is_(None))
    
    # Order by publication date (newest first)
    query = query.order_by(RSSArticle.published_at.desc())
    
    # Apply pagination
    total_count = query.count()
    articles = query.offset(skip).limit(limit).all()
    
    print(f"[API] Found {len(articles)} articles (total: {total_count})")
    return articles

@router.get("/{article_id}", response_model=ArticleInDB, summary="Get an article by ID")
def get_article(
    article_id: int = Path(..., description="ID of the article to retrieve"),
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific RSS article by ID.
    """
    print(f"[API] Fetching article with ID: {article_id}")
    
    article = db.query(RSSArticle).filter(
        RSSArticle.id == article_id,
        RSSArticle.deleted_at.is_(None)
    ).first()
    
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article with ID {article_id} not found"
        )
    
    return article

@router.get("/feed/{feed_id}", response_model=List[ArticleInDB], summary="Get articles by feed ID")
def get_articles_by_feed(
    feed_id: int = Path(..., description="ID of the feed"),
    skip: int = Query(0, description="Number of items to skip for pagination"),
    limit: int = Query(100, description="Maximum number of items to return"),
    db: Session = Depends(get_db)
):
    """
    Retrieve articles from a specific feed.
    """
    print(f"[API] Fetching articles for feed ID: {feed_id}")
    
    # Check if feed exists
    feed = db.query(RSSFeed).filter(
        RSSFeed.id == feed_id,
        RSSFeed.deleted_at.is_(None)
    ).first()
    
    if not feed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feed with ID {feed_id} not found"
        )
    
    # Get articles for this feed
    articles = db.query(RSSArticle).filter(
        RSSArticle.feed_id == feed_id,
        RSSArticle.deleted_at.is_(None)
    ).order_by(
        RSSArticle.published_at.desc()
    ).offset(skip).limit(limit).all()
    
    print(f"[API] Found {len(articles)} articles for feed ID: {feed_id}")
    return articles
