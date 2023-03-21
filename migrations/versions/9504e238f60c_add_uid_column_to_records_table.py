"""add UID column to records table

Revision ID: 9504e238f60c
Revises: b65a94548db2
Create Date: 2023-03-16 21:14:45.159504

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9504e238f60c'
down_revision = 'b65a94548db2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('records', sa.Column('uid', sa.TEXT))


def downgrade() -> None:
    op.drop_column('records', 'uid')
