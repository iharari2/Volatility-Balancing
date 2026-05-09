"""add anchor_price_before to trades

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-05-09

"""
from alembic import op
import sqlalchemy as sa

revision = 'c2d3e4f5a6b7'
down_revision = 'b1c2d3e4f5a6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('trades', sa.Column('anchor_price_before', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('trades', 'anchor_price_before')
