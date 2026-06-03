from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import BIGINT, DATE, DECIMAL, TEXT, TIMESTAMP, UUID as SQLUUID, VARCHAR, ForeignKey, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Security(Base):
    __tablename__ = "securities"

    ticker: Mapped[str] = mapped_column(VARCHAR(20), primary_key=True)
    company_name: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    sector: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    industry: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    country: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    currency: Mapped[str | None] = mapped_column(VARCHAR(20), nullable=True)
    exchange: Mapped[str | None] = mapped_column(VARCHAR(50), nullable=True)
    market_cap: Mapped[int | None] = mapped_column(BIGINT, nullable=True)
    last_updated: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)


class PriceHistory(Base):
    __tablename__ = "price_history"

    ticker: Mapped[str] = mapped_column(
        VARCHAR(20),
        ForeignKey("securities.ticker"),
        primary_key=True,
    )
    date: Mapped[date] = mapped_column(DATE, primary_key=True)
    open_price: Mapped[Decimal | None] = mapped_column(DECIMAL(18, 4), nullable=True)
    high_price: Mapped[Decimal | None] = mapped_column(DECIMAL(18, 4), nullable=True)
    low_price: Mapped[Decimal | None] = mapped_column(DECIMAL(18, 4), nullable=True)
    close_price: Mapped[Decimal | None] = mapped_column(DECIMAL(18, 4), nullable=True)
    volume: Mapped[int | None] = mapped_column(BIGINT, nullable=True)


class Product(Base):
    __tablename__ = "products"

    id: Mapped[UUID] = mapped_column(SQLUUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    slug: Mapped[str] = mapped_column(VARCHAR(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)


class Holding(Base):
    __tablename__ = "holdings"
    __table_args__ = (UniqueConstraint("product_id", "ticker", name="uq_holdings_product_id_ticker"),)

    id: Mapped[UUID] = mapped_column(SQLUUID(as_uuid=True), primary_key=True)
    product_id: Mapped[UUID] = mapped_column(
        SQLUUID(as_uuid=True),
        ForeignKey("products.id"),
        nullable=False,
    )
    ticker: Mapped[str] = mapped_column(VARCHAR(20), nullable=False)
    weight: Mapped[Decimal] = mapped_column(DECIMAL(8, 4), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
