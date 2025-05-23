"""Add string_id to rss_feeds

Revision ID: 20250509_add_feed_string_id
Revises: 20250508_initial
Create Date: 2025-05-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250509_add_feed_string_id'
down_revision = '20250508_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add string_id column to rss_feeds table
    op.add_column('rss_feeds', sa.Column('string_id', sa.String(100), nullable=True, unique=True))
    op.create_index('ix_rss_feeds_string_id', 'rss_feeds', ['string_id'])


def downgrade() -> None:
    # Remove string_id column from rss_feeds table
    op.drop_index('ix_rss_feeds_string_id', table_name='rss_feeds')
    op.drop_column('rss_feeds', 'string_id') 