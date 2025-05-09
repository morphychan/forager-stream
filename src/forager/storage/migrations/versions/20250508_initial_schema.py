"""Initial schema

Revision ID: 20250508_initial
Revises: 
Create Date: 2025-05-08 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '20250508_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create categories table
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(100), unique=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index('ix_categories_name', 'categories', ['name'])

    # Create tags table
    op.create_table(
        'tags',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(50), unique=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index('ix_tags_name', 'tags', ['name'])

    # Create rss_feeds table
    op.create_table(
        'rss_feeds',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('category_id', sa.Integer(), sa.ForeignKey('categories.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('url', sa.String(255), unique=True, nullable=False),
        sa.Column('poll_interval', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('last_error_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_rss_feeds_category_id', 'rss_feeds', ['category_id'])
    op.create_index('ix_rss_feeds_url', 'rss_feeds', ['url'])
    op.create_index('ix_rss_feeds_status', 'rss_feeds', ['status'])
    op.create_index('ix_rss_feeds_deleted_at', 'rss_feeds', ['deleted_at'])

    # Create feed_tags association table
    op.create_table(
        'feed_tags',
        sa.Column('feed_id', sa.Integer(), sa.ForeignKey('rss_feeds.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('tag_id', sa.Integer(), sa.ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True),
    )
    op.create_index('ix_feed_tags_feed_id', 'feed_tags', ['feed_id'])
    op.create_index('ix_feed_tags_tag_id', 'feed_tags', ['tag_id'])

    # Create rss_articles table (modified)
    op.create_table(
        'rss_articles',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('feed_id', sa.Integer(), sa.ForeignKey('rss_feeds.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('link', sa.String(500), unique=True, nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('fetched_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('manual_labels', sqlite.JSON(), nullable=True),
    )
    op.create_index('ix_rss_articles_feed_published', 'rss_articles', ['feed_id', 'published_at'])
    op.create_index('ix_rss_articles_fetched', 'rss_articles', ['fetched_at'])
    op.create_index('ix_rss_articles_link', 'rss_articles', ['link'])
    op.create_index('ix_rss_articles_status', 'rss_articles', ['status'])
    op.create_index('ix_rss_articles_deleted_at', 'rss_articles', ['deleted_at'])
    # Indexing JSON fields needs database-specific syntax.  Example for PostgreSQL:
    # op.create_index('ix_rss_articles_manual_labels', 'rss_articles', [sa.text('manual_labels')], postgresql_using='gin')

    # Create articles_tags association table
    op.create_table(
        'articles_tags',
        sa.Column('article_id', sa.Integer(), sa.ForeignKey('rss_articles.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('tag_id', sa.Integer(), sa.ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True),
    )
    op.create_index('ix_articles_tags_article_id', 'articles_tags', ['article_id'])
    op.create_index('ix_articles_tags_tag_id', 'articles_tags', ['tag_id'])


def downgrade() -> None:
    op.drop_index('ix_articles_tags_article_id', table_name='articles_tags')
    op.drop_index('ix_articles_tags_tag_id', table_name='articles_tags')
    op.drop_table('articles_tags')

    op.drop_index('ix_rss_articles_feed_published', table_name='rss_articles')
    op.drop_index('ix_rss_articles_fetched', table_name='rss_articles')
    op.drop_index('ix_rss_articles_link', table_name='rss_articles')
    op.drop_index('ix_rss_articles_status', table_name='rss_articles')
    op.drop_index('ix_rss_articles_deleted_at', table_name='rss_articles')
    # op.drop_index('ix_rss_articles_manual_labels', table_name='rss_articles')  # If you added a JSON index
    op.drop_table('rss_articles')

    op.drop_index('ix_feed_tags_feed_id', table_name='feed_tags')
    op.drop_index('ix_feed_tags_tag_id', table_name='feed_tags')
    op.drop_table('feed_tags')

    op.drop_index('ix_rss_feeds_category_id', table_name='rss_feeds')
    op.drop_index('ix_rss_feeds_url', table_name='rss_feeds')
    op.drop_index('ix_rss_feeds_status', table_name='rss_feeds')
    op.drop_index('ix_rss_feeds_deleted_at', table_name='rss_feeds')
    op.drop_table('rss_feeds')

    op.drop_index('ix_tags_name', table_name='tags')
    op.drop_table('tags')

    op.drop_index('ix_categories_name', table_name='categories')
    op.drop_table('categories')