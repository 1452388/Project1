"""add team member card fields (age, section, post, id_card)

Revision ID: f1a2b3c4d5e6
Revises: c1877597555c
Create Date: 2026-08-21

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = 'c1877597555c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('team_members') as batch_op:
        batch_op.add_column(sa.Column('age', sa.String(20), nullable=True, server_default=None))
        batch_op.add_column(sa.Column('section', sa.String(100), nullable=True, server_default=None))
        batch_op.add_column(sa.Column('post', sa.String(100), nullable=True, server_default=None))
        batch_op.add_column(sa.Column('id_card', sa.String(30), nullable=True, server_default=None))


def downgrade() -> None:
    with op.batch_alter_table('team_members') as batch_op:
        batch_op.drop_column('id_card')
        batch_op.drop_column('post')
        batch_op.drop_column('section')
        batch_op.drop_column('age')
