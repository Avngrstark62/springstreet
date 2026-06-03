from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator, model_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db import DuplicateSlugError, database
from factsheet_service import FactsheetResponse, build_factsheet_for_product
from logger import get_logger, log_error
from performance_service import PerformanceResponse, build_performance_for_product

router = APIRouter()
logger = get_logger(__name__)


@router.get("/health")
def health() -> dict[str, str]:
    try:
        database.health_check()
    except Exception as exc:
        log_error(logger, "Health check failed", exc)
        raise HTTPException(status_code=503, detail="Database unavailable")
    return {"status": "ok"}


def get_db():
    yield from database.session()


class CreateHoldingRequest(BaseModel):
    ticker: str
    weight: Decimal

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, value: str) -> str:
        ticker = value.strip().upper()
        if not ticker:
            raise ValueError("Ticker is required")
        if len(ticker) > 20:
            raise ValueError("Ticker must be 20 characters or less")
        return ticker

    @field_validator("weight")
    @classmethod
    def validate_weight(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("Weight must be greater than 0")
        if value > Decimal("100"):
            raise ValueError("Weight cannot exceed 100")
        return value


class CreateProductRequest(BaseModel):
    name: str
    slug: str
    description: str | None = None
    holdings: list[CreateHoldingRequest]

    @model_validator(mode="after")
    def validate_holdings(self) -> "CreateProductRequest":
        if not self.holdings:
            raise ValueError("At least one holding is required")

        tickers = [holding.ticker for holding in self.holdings]
        if len(tickers) != len(set(tickers)):
            raise ValueError("Duplicate tickers are not allowed")

        total_weight = sum((holding.weight for holding in self.holdings), Decimal("0"))
        if total_weight.quantize(Decimal("0.0001")) != Decimal("100.0000"):
            raise ValueError("Total holdings weight must equal 100.0000")

        return self


class ProductResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class HoldingResponse(BaseModel):
    id: UUID
    product_id: UUID
    ticker: str
    weight: Decimal
    created_at: datetime
    updated_at: datetime


@router.post("/products", response_model=ProductResponse)
def create_product(payload: CreateProductRequest, db: Session = Depends(get_db)) -> ProductResponse:
    now = datetime.utcnow()
    try:
        product = database.create_product_with_holdings(
            db,
            product_id=uuid4(),
            name=payload.name,
            slug=payload.slug,
            description=payload.description,
            created_at=now,
            updated_at=now,
            holdings=[(holding.ticker, holding.weight) for holding in payload.holdings],
        )
    except DuplicateSlugError as exc:
        log_error(logger, "Create product failed: duplicate slug", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except IntegrityError as exc:
        db.rollback()
        log_error(logger, "Create product failed due to integrity error", exc)
        if "products_slug_key" in str(exc.orig):
            raise HTTPException(status_code=400, detail=f"Product with slug '{payload.slug}' already exists") from exc
        raise HTTPException(status_code=400, detail="Could not create product due to data constraints") from exc
    except Exception as exc:
        db.rollback()
        log_error(logger, "Create product failed", exc)
        raise HTTPException(status_code=500, detail="Failed to create product")

    return ProductResponse.model_validate(product, from_attributes=True)


@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: UUID, db: Session = Depends(get_db)) -> ProductResponse:
    try:
        product = database.get_product(db, product_id)
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")
        return ProductResponse.model_validate(product, from_attributes=True)
    except HTTPException:
        raise
    except Exception as exc:
        log_error(logger, "Get product failed", exc)
        raise HTTPException(status_code=500, detail="Failed to get product")


@router.get("/products/slug/{slug}", response_model=ProductResponse)
def get_product_by_slug(slug: str, db: Session = Depends(get_db)) -> ProductResponse:
    try:
        product = database.get_product_by_slug(db, slug)
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")
        return ProductResponse.model_validate(product, from_attributes=True)
    except HTTPException:
        raise
    except Exception as exc:
        log_error(logger, "Get product by slug failed", exc)
        raise HTTPException(status_code=500, detail="Failed to get product by slug")


@router.get("/products", response_model=list[ProductResponse])
def get_products(db: Session = Depends(get_db)) -> list[ProductResponse]:
    try:
        products = database.get_products(db)
        return [ProductResponse.model_validate(product, from_attributes=True) for product in products]
    except Exception as exc:
        log_error(logger, "Get products failed", exc)
        raise HTTPException(status_code=500, detail="Failed to get products")


@router.get("/products/{product_id}/holdings", response_model=list[HoldingResponse])
def get_product_holdings(product_id: UUID, db: Session = Depends(get_db)) -> list[HoldingResponse]:
    try:
        product = database.get_product(db, product_id)
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")

        holdings = database.get_holdings_for_product(db, product_id)
        return [HoldingResponse.model_validate(holding, from_attributes=True) for holding in holdings]
    except HTTPException:
        raise
    except Exception as exc:
        log_error(logger, "Get holdings failed", exc)
        raise HTTPException(status_code=500, detail="Failed to get holdings")


@router.get("/products/{product_id}/factsheet", response_model=FactsheetResponse)
def get_product_factsheet(product_id: UUID, db: Session = Depends(get_db)) -> FactsheetResponse:
    try:
        return build_factsheet_for_product(db, product_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        log_error(logger, "Get factsheet failed", exc)
        raise HTTPException(status_code=500, detail="Failed to get factsheet")


@router.get("/products/{product_id}/performance", response_model=PerformanceResponse)
def get_product_performance(product_id: UUID, db: Session = Depends(get_db)) -> PerformanceResponse:
    try:
        return build_performance_for_product(db, product_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        log_error(logger, "Get performance failed", exc)
        raise HTTPException(status_code=500, detail="Failed to get performance")
