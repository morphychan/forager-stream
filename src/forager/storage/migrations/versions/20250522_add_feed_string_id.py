"""Add string_id to rss_feeds

Revision ID: 20250522_add_feed_string_id
Revises: 20250508_initial
Create Date: 2025-05-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = '20250522_add_feed_string_id'
down_revision = '20250508_initial'
branch_labels = None
depends_on = None


def column_exists(inspector, table_name, column_name):
    """Check if a column exists in the table."""
    columns = [c["name"] for c in inspector.get_columns(table_name)]
    return column_name in columns


def index_exists(inspector, table_name, index_name):
    """Check if an index exists in the table."""
    indexes = [idx["name"] for idx in inspector.get_indexes(table_name)]
    return index_name in indexes


def upgrade() -> None:
    # Get inspector for checking if column exists
    inspector = Inspector.from_engine(op.get_bind())
    
    # Only add column if it doesn't exist
    if not column_exists(inspector, 'rss_feeds', 'string_id'):
        # Add string_id column to rss_feeds table without UNIQUE constraint
        # SQLite doesn't support adding a column with constraints in ALTER TABLE
        op.add_column('rss_feeds', sa.Column('string_id', sa.String(100), nullable=True))
    
    # Only create index if it doesn't exist
    if not index_exists(inspector, 'rss_feeds', 'ix_rss_feeds_string_id'):
        # Create a unique index to enforce uniqueness
        op.create_index('ix_rss_feeds_string_id', 'rss_feeds', ['string_id'], unique=True)


def downgrade() -> None:
    # Drop index and column only if they exist
    inspector = Inspector.from_engine(op.get_bind())
    
    if index_exists(inspector, 'rss_feeds', 'ix_rss_feeds_string_id'):
        op.drop_index('ix_rss_feeds_string_id', table_name='rss_feeds')
    
    if column_exists(inspector, 'rss_feeds', 'string_id'):
        op.drop_column('rss_feeds', 'string_id') 