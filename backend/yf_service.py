from datetime import date

import pandas as pd
import yfinance as yf

from logger import get_logger

logger = get_logger(__name__)


def _null_if_na(value):
    return None if pd.isna(value) else value


def _volume_or_none(value):
    cleaned = _null_if_na(value)
    return None if cleaned is None else int(cleaned)


def _build_price_rows(price_frame) -> list[dict]:
    rows = []
    for index, row in price_frame.iterrows():
        row_date: date = index.date() if hasattr(index, "date") else index
        rows.append(
            {
                "date": row_date,
                "open_price": _null_if_na(row.get("Open")),
                "high_price": _null_if_na(row.get("High")),
                "low_price": _null_if_na(row.get("Low")),
                "close_price": _null_if_na(row.get("Close")),
                "volume": _volume_or_none(row.get("Volume")),
            }
        )
    return rows


def _extract_ticker_frames(downloaded, tickers: list[str]) -> dict[str, object]:
    if downloaded is None or downloaded.empty:
        return {}

    if len(tickers) == 1:
        return {tickers[0]: downloaded}

    ticker_frames: dict[str, object] = {}
    for ticker in tickers:
        if ticker in downloaded.columns.get_level_values(0):
            ticker_frames[ticker] = downloaded[ticker]
    return ticker_frames


def fetch_security_data(ticker: str) -> dict:
    stock = yf.Ticker(ticker)
    info = stock.info or {}

    return {
        "ticker": ticker,
        "company_name": info.get("longName") or info.get("shortName"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "country": info.get("country"),
        "currency": info.get("currency"),
        "exchange": info.get("exchange"),
        "market_cap": info.get("marketCap"),
    }


def fetch_security_data_for_tickers(tickers: list[str]) -> list[dict]:
    downloaded = yf.download(
        tickers=tickers,
        period="1d",
        interval="1d",
        group_by="ticker",
        progress=False,
        threads=True,
    )
    ticker_frames = _extract_ticker_frames(downloaded, tickers)
    if not ticker_frames:
        raise ValueError("No data returned from yfinance download")

    payloads: list[dict] = []
    for ticker in ticker_frames:
        payloads.append(
            {
                "ticker": ticker,
                "company_name": None,
                "sector": None,
                "industry": None,
                "country": None,
                "currency": None,
                "exchange": None,
                "market_cap": None,
            }
        )

    logger.info("Fetched security download data for %s tickers", len(payloads))
    return payloads


def fetch_price_history_for_tickers(
    tickers: list[str],
    *,
    range_period: str = "1y",
    interval: str = "1d",
) -> dict[str, list[dict]]:
    downloaded = yf.download(
        tickers=tickers,
        period=range_period,
        interval=interval,
        group_by="ticker",
        progress=False,
        threads=True,
    )
    ticker_frames = _extract_ticker_frames(downloaded, tickers)
    if not ticker_frames:
        raise ValueError("No price history returned from yfinance download")

    output: dict[str, list[dict]] = {}
    for ticker, frame in ticker_frames.items():
        rows = _build_price_rows(frame)
        if rows:
            output[ticker] = rows

    logger.info("Fetched price history download data for %s tickers", len(output))
    return output
