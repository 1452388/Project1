"""keep one active live code per project

Revision ID: d7f4a8c9210e
Revises: c4e2b1a7d903
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d7f4a8c9210e"
down_revision: Union[str, Sequence[str], None] = "c4e2b1a7d903"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()
    duplicate_projects = connection.execute(sa.text(
        """
        SELECT project_id
        FROM live_codes
        WHERE project_id IS NOT NULL AND is_deleted = 0
        GROUP BY project_id
        HAVING COUNT(*) > 1
        """
    )).scalars().all()

    for project_id in duplicate_projects:
        canonical_id = connection.execute(sa.text(
            """
            SELECT MIN(id)
            FROM live_codes
            WHERE project_id = :project_id AND is_deleted = 0
            """
        ), {"project_id": project_id}).scalar_one()
        connection.execute(sa.text(
            """
            UPDATE live_codes
            SET is_deleted = 1, is_active = 0
            WHERE project_id = :project_id
              AND is_deleted = 0
              AND id <> :canonical_id
            """
        ), {"project_id": project_id, "canonical_id": canonical_id})

    op.create_index(
        "uq_live_codes_active_project",
        "live_codes",
        ["project_id"],
        unique=True,
        sqlite_where=sa.text("project_id IS NOT NULL AND is_deleted = 0"),
        postgresql_where=sa.text("project_id IS NOT NULL AND is_deleted = false"),
    )


def downgrade() -> None:
    op.drop_index("uq_live_codes_active_project", table_name="live_codes")