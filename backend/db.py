from collections.abc import Generator, Sequence
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from config import settings
from models import Holding, PriceHistory, Product, Security


class DuplicateSlugError(Exception):
    pass


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

    def upsert_security(
        self,
        db: Session,
        *,
        ticker: str,
        company_name: str | None = None,
        sector: str | None = None,
        industry: str | None = None,
        country: str | None = None,
        currency: str | None = None,
        exchange: str | None = None,
        market_cap: int | None = None,
        last_updated: datetime,
    ) -> Security:
        security = db.get(Security, ticker)
        if security is None:
            security = Security(ticker=ticker)
            db.add(security)

        security.company_name = company_name
        security.sector = sector
        security.industry = industry
        security.country = country
        security.currency = currency
        security.exchange = exchange
        security.market_cap = market_cap
        security.last_updated = last_updated

        db.commit()
        db.refresh(security)
        return security

    # Price history CRUD
    def get_price_history(self, db: Session, ticker: str) -> Sequence[PriceHistory]:
        return (
            db.query(PriceHistory)
            .filter(PriceHistory.ticker == ticker)
            .order_by(PriceHistory.date.desc())
            .all()
        )

    def upsert_price_history(
        self,
        db: Session,
        *,
        ticker: str,
        day: date,
        open_price: Decimal | None = None,
        high_price: Decimal | None = None,
        low_price: Decimal | None = None,
        close_price: Decimal | None = None,
        volume: int | None = None,
    ) -> PriceHistory:
        record = db.get(PriceHistory, {"ticker": ticker, "date": day})
        if record is None:
            record = PriceHistory(ticker=ticker, date=day)
            db.add(record)

        record.open_price = open_price
        record.high_price = high_price
        record.low_price = low_price
        record.close_price = close_price
        record.volume = volume

        db.commit()
        db.refresh(record)
        return record

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
