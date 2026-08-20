"""add team members table

Revision ID: e2f5a6b7c8d9
Revises: d7f4a8c9210e
Create Date: 2026-08-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e2f5a6b7c8d9"
down_revision: Union[str, Sequence[str], None] = "d7f4a8c9210e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "team_members",
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("position", sa.String(100), nullable=True),
        sa.Column("department", sa.String(100), nullable=True),
        sa.Column("email", sa.String(200), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("wechat", sa.String(100), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("code", sa.String(16), nullable=False),
        sa.Column("status", sa.String(20), server_default="active", nullable=False),
        sa.Column("edit_password_hash", sa.String(255), nullable=True),
        sa.Column("extra_data", sa.JSON(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default="0", nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_team_members_code", "team_members", ["code"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_team_members_code", table_name="team_members")
    op.drop_table("team_members")
