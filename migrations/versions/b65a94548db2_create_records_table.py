"""create records table

Revision ID: b65a94548db2
Revises:
Create Date: 2023-02-22 18:10:09.766542

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b65a94548db2"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "records",
        sa.Column("sid", sa.TEXT),
        sa.Column("ts", sa.TIMESTAMP(timezone=True)),
        sa.Column("code", sa.TEXT),
        sa.Column("duration", sa.INTEGER),
        sa.Column("energy", sa.INTEGER),
        sa.Column("start", sa.TIMESTAMP(timezone=True)),
        sa.Column("finish", sa.TIMESTAMP(timezone=True)),
    )
    op.execute(sa.text("select create_hypertable('records', 'ts')"))


def downgrade() -> None:
    op.drop_table("records")
