import json

import yfinance as yf


def fetch_tickers_data(tickers: list[str]) -> dict:
    result = {}

    # Fetch historical data for all tickers in one call
    history_df = yf.download(
        tickers=tickers,
        period="1mo",
        auto_adjust=False,
        group_by="ticker",
        progress=False,
    )

    for ticker in tickers:
        # Metadata (still fetched per ticker)
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
        except Exception:
            info = {}

        metadata = {
            "ticker": ticker,
            "company_name": info.get("longName"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "country": info.get("country"),
            "market_cap": info.get("marketCap"),
            "currency": info.get("currency"),
            "exchange": info.get("exchange"),
            "website": info.get("website"),
            "employee_count": info.get("fullTimeEmployees"),
        }

        # Extract this ticker's history from the bulk download
        try:
            ticker_history = history_df[ticker]
            history_json = json.loads(
                ticker_history.reset_index().to_json(
                    orient="records",
                    date_format="iso"
                )
            )
        except Exception:
            history_json = []

        result[ticker] = {
            "metadata": metadata,
            "price_history": history_json,
        }

    return result


if __name__ == "__main__":
    tickers = ["AAPL", "MSFT", "NVDA", "CSK"]

    try:
        data = fetch_tickers_data(tickers)

        print(json.dumps(data, indent=2))

    except Exception as exc:
        print(f"Unexpected error: {exc}")
