"""Initial schema

Revision ID: 20250508_initial
Revises: 
Create Date: 2025-05-08 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250508_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create rss_articles table
    op.create_table(
        'rss_articles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('feed_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('link', sa.String(), nullable=False),
        sa.Column('published', sa.DateTime(), nullable=False),
        sa.Column('fetched_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('link')
    )
    
    # Create indexes
    op.create_index('ix_rss_articles_feed_id', 'rss_articles', ['feed_id'])
    op.create_index('ix_rss_articles_published', 'rss_articles', ['published'])


def downgrade() -> None:
    op.drop_index('ix_rss_articles_published', table_name='rss_articles')
    op.drop_index('ix_rss_articles_feed_id', table_name='rss_articles')
    op.drop_table('rss_articles') 