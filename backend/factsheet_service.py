from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import database
from models import Holding, Product, Security


class FactsheetProductResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str | None


class LargestHoldingResponse(BaseModel):
    ticker: str
    weight: Decimal


class FactsheetSummaryResponse(BaseModel):
    holdings_count: int
    largest_holding: LargestHoldingResponse | None


class TopHoldingResponse(BaseModel):
    ticker: str
    company_name: str
    weight: Decimal


class SectorExposureResponse(BaseModel):
    sector: str
    weight: Decimal


class CountryExposureResponse(BaseModel):
    country: str
    weight: Decimal


class MarketCapExposureResponse(BaseModel):
    bucket: str
    weight: Decimal


class FactsheetResponse(BaseModel):
    product: FactsheetProductResponse
    summary: FactsheetSummaryResponse
    top_holdings: list[TopHoldingResponse]
    sector_exposure: list[SectorExposureResponse]
    country_exposure: list[CountryExposureResponse]
    market_cap_exposure: list[MarketCapExposureResponse]
    last_updated: datetime


def _market_cap_bucket(market_cap: int | None) -> str:
    if market_cap is None:
        return "Unknown"
    if market_cap > 10_000_000_000:
        return "Large Cap"
    if market_cap >= 2_000_000_000:
        return "Mid Cap"
    return "Small Cap"


def _accumulate_weight(
    totals: dict[str, Decimal],
    *,
    key: str,
    weight: Decimal,
) -> None:
    totals[key] = totals.get(key, Decimal("0")) + weight


def _sorted_weight_rows(values: dict[str, Decimal]) -> list[tuple[str, Decimal]]:
    return sorted(values.items(), key=lambda item: (-item[1], item[0]))


def build_factsheet_for_product(db: Session, product_id: UUID) -> FactsheetResponse:
    product: Product | None = database.get_product(db, product_id)
    if product is None:
        raise ValueError("Product not found")

    rows = database.get_holdings_with_securities(db, product_id)
    holdings_with_securities: list[tuple[Holding, Security | None]] = list(rows)

    ordered_rows = sorted(holdings_with_securities, key=lambda row: (-row[0].weight, row[0].ticker))
    top_holdings = [
        TopHoldingResponse(
            ticker=holding.ticker,
            company_name=(security.company_name if security and security.company_name else holding.ticker),
            weight=holding.weight,
        )
        for holding, security in ordered_rows
    ]

    sector_totals: dict[str, Decimal] = {}
    country_totals: dict[str, Decimal] = {}
    market_cap_totals: dict[str, Decimal] = {}
    last_updated_values: list[datetime] = []

    for holding, security in holdings_with_securities:
        sector = security.sector if security and security.sector else "Unknown"
        country = security.country if security and security.country else "Unknown"
        market_cap_bucket = _market_cap_bucket(security.market_cap if security else None)

        _accumulate_weight(sector_totals, key=sector, weight=holding.weight)
        _accumulate_weight(country_totals, key=country, weight=holding.weight)
        _accumulate_weight(market_cap_totals, key=market_cap_bucket, weight=holding.weight)

        if security and security.last_updated:
            last_updated_values.append(security.last_updated)

    largest_holding = (
        LargestHoldingResponse(ticker=ordered_rows[0][0].ticker, weight=ordered_rows[0][0].weight) if ordered_rows else None
    )

    return FactsheetResponse(
        product=FactsheetProductResponse.model_validate(product, from_attributes=True),
        summary=FactsheetSummaryResponse(
            holdings_count=len(holdings_with_securities),
            largest_holding=largest_holding,
        ),
        top_holdings=top_holdings,
        sector_exposure=[SectorExposureResponse(sector=key, weight=weight) for key, weight in _sorted_weight_rows(sector_totals)],
        country_exposure=[
            CountryExposureResponse(country=key, weight=weight) for key, weight in _sorted_weight_rows(country_totals)
        ],
        market_cap_exposure=[
            MarketCapExposureResponse(bucket=key, weight=weight) for key, weight in _sorted_weight_rows(market_cap_totals)
        ],
        last_updated=max(last_updated_values) if last_updated_values else datetime.utcnow(),
    )
