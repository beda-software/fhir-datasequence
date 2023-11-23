"""Add unique constaint to workouts table

Revision ID: b48df1f110f3
Revises: 5d3300030073
Create Date: 2023-11-23 13:51:22.876028

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "b48df1f110f3"
down_revision = "5d3300030073"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint("workout_ts_user_uq", "records", ["ts", "uid"])


def downgrade() -> None:
    op.drop_constraint("workout_ts_user_uq", "records")
