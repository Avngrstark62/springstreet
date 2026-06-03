from datetime import date, datetime, time, timedelta
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import database
from models import Holding, PriceHistory, Product


class PerformanceProductResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str | None


class PerformanceReturnsResponse(BaseModel):
    one_month: Decimal
    three_month: Decimal
    one_year: Decimal


class PortfolioChartPointResponse(BaseModel):
    date: date
    value: Decimal


class PerformanceResponse(BaseModel):
    product: PerformanceProductResponse
    returns: PerformanceReturnsResponse
    portfolio_growth_chart: list[PortfolioChartPointResponse]
    last_updated: datetime


def _group_price_history(rows: list[PriceHistory]) -> dict[str, list[tuple[date, Decimal]]]:
    grouped: dict[str, list[tuple[date, Decimal]]] = {}
    for row in rows:
        if row.close_price is None:
            continue
        grouped.setdefault(row.ticker, []).append((row.date, row.close_price))
    return grouped


def _close_on_or_before(points: list[tuple[date, Decimal]], target_date: date) -> Decimal | None:
    candidate: Decimal | None = None
    for point_date, close in points:
        if point_date > target_date:
            break
        candidate = close
    return candidate


def _weighted_return(
    holdings: list[Holding],
    prices_by_ticker: dict[str, list[tuple[date, Decimal]]],
    *,
    days: int,
) -> Decimal:
    today = date.today()
    reference_date = today - timedelta(days=days)
    total = Decimal("0")

    for holding in holdings:
        points = prices_by_ticker.get(holding.ticker, [])
        if not points:
            continue

        current_close = points[-1][1]
        old_close = _close_on_or_before(points, reference_date)
        if old_close is None or old_close == 0:
            continue

        stock_return = (current_close / old_close) - Decimal("1")
        total += (holding.weight / Decimal("100")) * stock_return

    return total


def _build_portfolio_growth_chart(
    holdings: list[Holding],
    prices_by_ticker: dict[str, list[tuple[date, Decimal]]],
) -> list[PortfolioChartPointResponse]:
    all_dates = sorted({point_date for points in prices_by_ticker.values() for point_date, _ in points})
    if not all_dates:
        return []

    weights = {holding.ticker: (holding.weight / Decimal("100")) for holding in holdings}
    bases = {ticker: points[0][1] for ticker, points in prices_by_ticker.items() if points}
    current_idx_by_ticker = {ticker: 0 for ticker in prices_by_ticker}

    points_by_ticker_date = {
        ticker: {point_date: close for point_date, close in points} for ticker, points in prices_by_ticker.items()
    }

    current_close_by_ticker: dict[str, Decimal] = {}
    chart: list[PortfolioChartPointResponse] = []

    for day in all_dates:
        for ticker, points in prices_by_ticker.items():
            index = current_idx_by_ticker[ticker]
            while index + 1 < len(points) and points[index + 1][0] <= day:
                index += 1
            current_idx_by_ticker[ticker] = index
            point_date = points[index][0]
            if point_date <= day:
                current_close_by_ticker[ticker] = points_by_ticker_date[ticker][point_date]

        multiplier = Decimal("0")
        for ticker, weight in weights.items():
            base = bases.get(ticker)
            current = current_close_by_ticker.get(ticker)
            if base is None or base == 0 or current is None:
                multiplier += weight
                continue
            multiplier += weight * (current / base)

        chart.append(PortfolioChartPointResponse(date=day, value=Decimal("100") * multiplier))

    return chart


def build_performance_for_product(db: Session, product_id: UUID) -> PerformanceResponse:
    product: Product | None = database.get_product(db, product_id)
    if product is None:
        raise ValueError("Product not found")

    holdings = list(database.get_holdings_for_product(db, product_id))
    tickers = [holding.ticker for holding in holdings]

    start_date = date.today() - timedelta(days=370)
    price_rows = list(database.get_price_history_for_tickers(db, tickers, start_date=start_date))
    prices_by_ticker = _group_price_history(price_rows)

    one_month = _weighted_return(holdings, prices_by_ticker, days=30)
    three_month = _weighted_return(holdings, prices_by_ticker, days=90)
    one_year = _weighted_return(holdings, prices_by_ticker, days=365)
    chart = _build_portfolio_growth_chart(holdings, prices_by_ticker)

    latest_price_date = max((point_date for points in prices_by_ticker.values() for point_date, _ in points), default=None)
    last_updated = datetime.combine(latest_price_date, time.min) if latest_price_date else datetime.utcnow()

    return PerformanceResponse(
        product=PerformanceProductResponse.model_validate(product, from_attributes=True),
        returns=PerformanceReturnsResponse(one_month=one_month, three_month=three_month, one_year=one_year),
        portfolio_growth_chart=chart,
        last_updated=last_updated,
    )
