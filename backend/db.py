from collections.abc import Generator, Sequence
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, TypedDict
from uuid import UUID, uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from config import settings
from models import Holding, PriceHistory, Product, Security


class DuplicateSlugError(Exception):
    pass


class SecurityRecord(TypedDict, total=False):
    ticker: str
    company_name: str | None
    sector: str | None
    industry: str | None
    country: str | None
    currency: str | None
    exchange: str | None
    market_cap: int | None
    last_updated: datetime


class PriceHistoryRecord(TypedDict, total=False):
    ticker: str
    date: date
    open_price: Decimal | float | int | None
    high_price: Decimal | float | int | None
    low_price: Decimal | float | int | None
    close_price: Decimal | float | int | None
    volume: int | float | None


class Database:
    _instance: Optional["Database"] = None

    def __new__(cls) -> "Database":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._setup()
        return cls._instance

    def _setup(self) -> None:
        connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
        self.engine: Engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            connect_args=connect_args,
            hide_parameters=True,
        )
        self.session_local = sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    def session(self) -> Generator[Session, None, None]:
        db = self.session_local()
        try:
            yield db
        finally:
            db.close()

    def health_check(self) -> bool:
        with self.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True

    # Securities CRUD
    def get_security(self, db: Session, ticker: str) -> Security | None:
        return db.get(Security, ticker)

    # Price history CRUD
    def get_price_history(self, db: Session, ticker: str) -> Sequence[PriceHistory]:
        return (
            db.query(PriceHistory)
            .filter(PriceHistory.ticker == ticker)
            .order_by(PriceHistory.date.desc())
            .all()
        )

    # Products CRUD
    def get_product(self, db: Session, product_id: UUID) -> Product | None:
        return db.get(Product, product_id)

    def get_product_by_slug(self, db: Session, slug: str) -> Product | None:
        return db.query(Product).filter(Product.slug == slug).first()

    def get_products(self, db: Session) -> Sequence[Product]:
        return db.query(Product).order_by(Product.created_at.desc()).all()

    def create_product(
        self,
        db: Session,
        *,
        product_id: UUID,
        name: str,
        slug: str,
        description: str | None,
        created_at: datetime,
        updated_at: datetime,
    ) -> Product:
        product = Product(
            id=product_id,
            name=name,
            slug=slug,
            description=description,
            created_at=created_at,
            updated_at=updated_at,
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        return product

    def create_product_with_holdings(
        self,
        db: Session,
        *,
        product_id: UUID,
        name: str,
        slug: str,
        description: str | None,
        created_at: datetime,
        updated_at: datetime,
        holdings: Sequence[tuple[str, Decimal]],
    ) -> Product:
        existing = self.get_product_by_slug(db, slug)
        if existing is not None:
            raise DuplicateSlugError(f"Product with slug '{slug}' already exists")

        product = Product(
            id=product_id,
            name=name,
            slug=slug,
            description=description,
            created_at=created_at,
            updated_at=updated_at,
        )

        with db.begin():
            db.add(product)
            # Ensure product row is written before holdings inserts.
            db.flush()
            for ticker, weight in holdings:
                db.add(
                    Holding(
                        id=uuid4(),
                        product_id=product_id,
                        ticker=ticker,
                        weight=weight,
                        created_at=created_at,
                        updated_at=updated_at,
                    )
                )

        db.refresh(product)
        return product

    def upsert_product(
        self,
        db: Session,
        *,
        product_id: UUID,
        name: str,
        slug: str,
        description: str | None,
        created_at: datetime,
        updated_at: datetime,
    ) -> Product:
        product = db.get(Product, product_id)
        if product is None:
            product = Product(id=product_id)
            db.add(product)

        product.name = name
        product.slug = slug
        product.description = description
        product.created_at = created_at
        product.updated_at = updated_at

        db.commit()
        db.refresh(product)
        return product

    # Holdings CRUD
    def get_holdings_for_product(self, db: Session, product_id: UUID) -> Sequence[Holding]:
        return db.query(Holding).filter(Holding.product_id == product_id).all()

    def get_unique_holding_tickers(self, db: Session) -> list[str]:
        rows = db.query(Holding.ticker).distinct().all()
        return sorted(row[0] for row in rows if row[0])

    def bulk_upsert_securities(self, db: Session, records: Sequence[SecurityRecord]) -> int:
        now = datetime.utcnow()
        values = [
            {
                "ticker": record["ticker"],
                "company_name": record.get("company_name"),
                "sector": record.get("sector"),
                "industry": record.get("industry"),
                "country": record.get("country"),
                "currency": record.get("currency"),
                "exchange": record.get("exchange"),
                "market_cap": record.get("market_cap"),
                "last_updated": record.get("last_updated") or now,
            }
            for record in records
            if record.get("ticker")
        ]
        if not values:
            return 0

        stmt = insert(Security).values(values)
        stmt = stmt.on_conflict_do_update(
            index_elements=[Security.ticker],
            set_={
                "company_name": stmt.excluded.company_name,
                "sector": stmt.excluded.sector,
                "industry": stmt.excluded.industry,
                "country": stmt.excluded.country,
                "currency": stmt.excluded.currency,
                "exchange": stmt.excluded.exchange,
                "market_cap": stmt.excluded.market_cap,
                "last_updated": stmt.excluded.last_updated,
            },
        )
        db.execute(stmt)
        db.commit()
        return len(values)

    def bulk_upsert_price_history(self, db: Session, records: Sequence[PriceHistoryRecord]) -> int:
        values = [
            {
                "ticker": record["ticker"],
                "date": record["date"],
                "open_price": record.get("open_price"),
                "high_price": record.get("high_price"),
                "low_price": record.get("low_price"),
                "close_price": record.get("close_price"),
                "volume": record.get("volume"),
            }
            for record in records
            if record.get("ticker") and record.get("date") is not None
        ]
        if not values:
            return 0

        stmt = insert(PriceHistory).values(values)
        stmt = stmt.on_conflict_do_update(
            index_elements=[PriceHistory.ticker, PriceHistory.date],
            set_={
                "open_price": stmt.excluded.open_price,
                "high_price": stmt.excluded.high_price,
                "low_price": stmt.excluded.low_price,
                "close_price": stmt.excluded.close_price,
                "volume": stmt.excluded.volume,
            },
        )
        db.execute(stmt)
        db.commit()
        return len(values)

    def upsert_holding(
        self,
        db: Session,
        *,
        holding_id: UUID,
        product_id: UUID,
        ticker: str,
        weight: Decimal,
        created_at: datetime,
        updated_at: datetime,
    ) -> Holding:
        holding = db.get(Holding, holding_id)
        if holding is None:
            holding = Holding(id=holding_id)
            db.add(holding)

        holding.product_id = product_id
        holding.ticker = ticker
        holding.weight = weight
        holding.created_at = created_at
        holding.updated_at = updated_at

        db.commit()
        db.refresh(holding)
        return holding


database = Database()
