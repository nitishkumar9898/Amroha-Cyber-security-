"""add OSINTForge tables

Revision ID: 20261019121500
Revises: 20261019120000
Create Date: 2026-10-19 12:15:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20261019121500'
down_revision = '20261019120000'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'social_post',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('platform', sa.String(length=50), nullable=False),
        sa.Column('post_id', sa.String(length=200), nullable=False),
        sa.Column('content', sa.JSON(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('author_hash', sa.String(length=64), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=True),
        sa.Column('raw_json', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('post_id')
    )
    op.create_table(
        'actor_profile',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name_hash', sa.String(length=64), nullable=False),
        sa.Column('platforms', sa.JSON(), nullable=True),
        sa.Column('affiliations', sa.JSON(), nullable=True),
        sa.Column('risk_score', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name_hash')
    )
    op.create_table(
        'misinformation_event',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('claim_text', sa.String(length=500), nullable=False),
        sa.Column('fact_check_url', sa.String(length=500), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('detected_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['post_id'], ['social_post.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'crawl_job',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('platform', sa.String(length=50), nullable=False),
        sa.Column('query', sa.String(length=200), nullable=False),
        sa.Column('schedule', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('crawl_job')
    op.drop_table('misinformation_event')
    op.drop_table('actor_profile')
    op.drop_table('social_post')
