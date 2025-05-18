"""
API routes for RSS articles.
"""
from typing import List, Optional, Dict, Any
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
    manual_labels: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

class ArticleUpdate(BaseModel):
    """Model for updating article data."""
    manual_labels: Optional[Dict[str, Any]] = None

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
    Retrieve a specific RSS article by ID. If summary/content is missing, fetch and update it on demand.
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
    
    # get feed url by feed_id
    feed = db.query(RSSFeed).filter(RSSFeed.id == article.feed_id).first()
    if not feed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feed with ID {article.feed_id} not found"
        )
    feed_url = feed.url
    
    # lazy load summary/content (only load when summary is empty)
    no_content_reason = None
    if not article.summary:
        try:
            from src.forager.input.rss import RSSFetcher
            fetcher = RSSFetcher(feed_url)
            fetched_articles = fetcher.fetch(include_details=True)
            matched = next((a for a in fetched_articles if a.get("link") == article.link), None)
            if matched:
                summary = matched.get("summary")
                content = matched.get("content")
                if summary or content:
                    article.summary = summary
                    article.content = content
                    db.commit()
                    print(f"[API] Updated article {article_id} with fetched summary/content.")
                else:
                    print(f"[API] No summary/content available in RSS entry; not updating.")
                    no_content_reason = "No summary/content in RSS entry."
            else:
                print(f"[API] No matching article found for link: {article.link}")
                no_content_reason = "No matching article found in RSS feed."
        except Exception as e:
            print(f"[API] Error fetching summary/content for article {article_id}: {e}")
            no_content_reason = f"Error fetching content: {e}"
    # return with no_content_reason field
    result = article
    if no_content_reason:
        result = article.__dict__.copy()
        result["no_content_reason"] = no_content_reason
    return result

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

@router.patch("/{article_id}", response_model=ArticleInDB, summary="Update an article")
def update_article(
    article_id: int = Path(..., description="ID of the article to update"),
    update_data: ArticleUpdate = None,
    db: Session = Depends(get_db)
):
    """
    Update a specific RSS article by ID.
    """
    print(f"[API] Updating article with ID: {article_id}")
    
    article = db.query(RSSArticle).filter(
        RSSArticle.id == article_id,
        RSSArticle.deleted_at.is_(None)
    ).first()
    
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article with ID {article_id} not found"
        )
    
    try:
        if update_data.manual_labels is not None:
            article.manual_labels = update_data.manual_labels
        db.commit()
        db.refresh(article)
        return article
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update article: {str(e)}"
        )
