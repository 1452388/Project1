"""add project table

Revision ID: c1d2e3f4a5b6
Revises: 8b5b2ab3657f
Create Date: 2026-08-19

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c1d2e3f4a5b6'
down_revision = '8b5b2ab3657f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('content_style', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('cover_image', sa.String(500), nullable=True),
        sa.Column('attachments', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('extra_data', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('projects')
