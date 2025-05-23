"""
SQLAlchemy models for the Forager database.

This module defines the ORM models that map to our database tables.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Table
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


# Association tables
feed_tags = Table(
    'feed_tags',
    Base.metadata,
    Column('feed_id', Integer, ForeignKey('rss_feeds.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)

articles_tags = Table(
    'articles_tags',
    Base.metadata,
    Column('article_id', Integer, ForeignKey('rss_articles.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)


class Category(Base):
    """Model for feed categories."""
    __tablename__ = 'categories'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    feeds: Mapped[List['RSSFeed']] = relationship(back_populates='category')


class Tag(Base):
    """Model for tags that can be applied to feeds and articles."""
    __tablename__ = 'tags'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    feeds: Mapped[List['RSSFeed']] = relationship(secondary=feed_tags, back_populates='tags')
    articles: Mapped[List['RSSArticle']] = relationship(secondary=articles_tags, back_populates='tags')


class RSSFeed(Base):
    """Model for RSS feeds."""
    __tablename__ = 'rss_feeds'

    id: Mapped[int] = mapped_column(primary_key=True)
    string_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    category_id: Mapped[int] = mapped_column(ForeignKey('categories.id', ondelete='CASCADE'), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    poll_interval: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_error_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    category: Mapped['Category'] = relationship(back_populates='feeds')
    tags: Mapped[List['Tag']] = relationship(secondary=feed_tags, back_populates='feeds')
    articles: Mapped[List['RSSArticle']] = relationship(back_populates='feed')


class RSSArticle(Base):
    """Model for RSS articles."""
    __tablename__ = 'rss_articles'

    id: Mapped[int] = mapped_column(primary_key=True)
    feed_id: Mapped[int] = mapped_column(ForeignKey('rss_feeds.id', ondelete='CASCADE'), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    link: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    manual_labels: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    feed: Mapped['RSSFeed'] = relationship(back_populates='articles')
    tags: Mapped[List['Tag']] = relationship(secondary=articles_tags, back_populates='articles') 