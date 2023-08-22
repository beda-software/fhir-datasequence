"""create metriport unhandled data table

Revision ID: 5d3300030073
Revises: e537d7dbd899
Create Date: 2023-08-22 09:48:51.784647

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = "5d3300030073"
down_revision = "e537d7dbd899"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "metriport_unhandled_data",
        sa.Column("ts", sa.TIMESTAMP(timezone=True)),
        sa.Column("uid", sa.TEXT),
        sa.Column("data", JSONB),
    )

    op.execute(sa.text("select create_hypertable('metriport_unhandled_data', 'ts')"))


def downgrade() -> None:
    op.drop_table("metriport_unhandled_data")
