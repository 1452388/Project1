"""add project target to live codes

Revision ID: c4e2b1a7d903
Revises: 8b5b2ab3657f
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4e2b1a7d903"
down_revision: Union[str, Sequence[str], None] = "c1d2e3f4a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("live_codes", "article_id", existing_type=sa.Integer(), nullable=True)
    op.add_column("live_codes", sa.Column("project_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_live_codes_project_id_projects", "live_codes", "projects", ["project_id"], ["id"]
    )
    op.create_index("ix_live_codes_project_id", "live_codes", ["project_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_live_codes_project_id", table_name="live_codes")
    op.drop_constraint("fk_live_codes_project_id_projects", "live_codes", type_="foreignkey")
    op.drop_column("live_codes", "project_id")
    op.alter_column("live_codes", "article_id", existing_type=sa.Integer(), nullable=False)