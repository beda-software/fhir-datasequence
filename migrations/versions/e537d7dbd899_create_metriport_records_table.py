"""create metriport records table

Revision ID: e537d7dbd899
Revises: 9504e238f60c
Create Date: 2023-08-18 14:27:16.852473

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e537d7dbd899"
down_revision = "9504e238f60c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "metriport_records",
        sa.Column("sid", sa.TEXT),
        sa.Column("ts", sa.TIMESTAMP(timezone=True)),
        sa.Column("code", sa.TEXT),
        sa.Column("duration", sa.INTEGER),
        sa.Column("energy", sa.INTEGER),
        sa.Column("start", sa.TIMESTAMP(timezone=True)),
        sa.Column("finish", sa.TIMESTAMP(timezone=True)),
        sa.Column("provider", sa.TEXT),
    )
    op.execute(sa.text("select create_hypertable('metriport_records', 'ts')"))


def downgrade() -> None:
    op.drop_table("metriport_records")
