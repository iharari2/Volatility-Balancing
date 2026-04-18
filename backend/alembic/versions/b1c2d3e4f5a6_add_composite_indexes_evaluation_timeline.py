"""add composite indexes evaluation timeline

Revision ID: b1c2d3e4f5a6
Revises: 4e10243479c7
Create Date: 2026-04-18

Reduces DB transfer by letting Postgres use composite indexes for the
most common list_by_position and list_by_portfolio query patterns instead
of scanning individual single-column indexes.
"""
from alembic import op

revision = 'b1c2d3e4f5a6'
down_revision = '4e10243479c7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        'ix_eval_timeline_pos_mode_ts',
        'position_evaluation_timeline',
        ['position_id', 'mode', 'timestamp'],
    )
    op.create_index(
        'ix_eval_timeline_portfolio_mode_ts',
        'position_evaluation_timeline',
        ['tenant_id', 'portfolio_id', 'mode', 'timestamp'],
    )


def downgrade() -> None:
    op.drop_index('ix_eval_timeline_pos_mode_ts', table_name='position_evaluation_timeline')
    op.drop_index('ix_eval_timeline_portfolio_mode_ts', table_name='position_evaluation_timeline')
