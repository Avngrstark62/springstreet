"""create initial market and product tables

Revision ID: 20260603_01
Revises:
Create Date: 2026-06-03 21:28:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260603_01"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "securities",
        sa.Column("ticker", sa.VARCHAR(length=20), primary_key=True, nullable=False),
        sa.Column("company_name", sa.VARCHAR(length=255), nullable=True),
        sa.Column("sector", sa.VARCHAR(length=255), nullable=True),
        sa.Column("industry", sa.VARCHAR(length=255), nullable=True),
        sa.Column("country", sa.VARCHAR(length=255), nullable=True),
        sa.Column("currency", sa.VARCHAR(length=20), nullable=True),
        sa.Column("exchange", sa.VARCHAR(length=50), nullable=True),
        sa.Column("market_cap", sa.BIGINT(), nullable=True),
        sa.Column("last_updated", sa.TIMESTAMP(), nullable=False),
    )

    op.create_table(
        "price_history",
        sa.Column("ticker", sa.VARCHAR(length=20), nullable=False),
        sa.Column("date", sa.DATE(), nullable=False),
        sa.Column("open_price", sa.DECIMAL(precision=18, scale=4), nullable=True),
        sa.Column("high_price", sa.DECIMAL(precision=18, scale=4), nullable=True),
        sa.Column("low_price", sa.DECIMAL(precision=18, scale=4), nullable=True),
        sa.Column("close_price", sa.DECIMAL(precision=18, scale=4), nullable=True),
        sa.Column("volume", sa.BIGINT(), nullable=True),
        sa.ForeignKeyConstraint(["ticker"], ["securities.ticker"]),
        sa.PrimaryKeyConstraint("ticker", "date"),
    )

    op.create_table(
        "products",
        sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
        sa.Column("name", sa.VARCHAR(length=255), nullable=False),
        sa.Column("slug", sa.VARCHAR(length=255), nullable=False, unique=True),
        sa.Column("description", sa.TEXT(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(), nullable=False),
    )

    op.create_table(
        "holdings",
        sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
        sa.Column("product_id", sa.UUID(), nullable=False),
        sa.Column("ticker", sa.VARCHAR(length=20), nullable=False),
        sa.Column("weight", sa.DECIMAL(precision=8, scale=4), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.UniqueConstraint("product_id", "ticker", name="uq_holdings_product_id_ticker"),
    )


def downgrade() -> None:
    op.drop_table("holdings")
    op.drop_table("products")
    op.drop_table("price_history")
    op.drop_table("securities")
