import json

import yfinance as yf


def fetch_ticker_data(ticker: str) -> dict:
    stock = yf.Ticker(ticker)

    # Historical price data
    history = stock.history(period="1mo")
    history_json = json.loads(
        history.reset_index().to_json(
            orient="records",
            date_format="iso"
        )
    )

    # Metadata
    try:
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

    return {
        "metadata": metadata,
        "price_history": history_json,
    }


if __name__ == "__main__":
    ticker = "AAPL"

    try:
        data = fetch_ticker_data(ticker)

        print("\n=== METADATA ===\n")
        print(json.dumps(data["metadata"], indent=2))

        print("\n=== PRICE HISTORY ===\n")
        print(json.dumps(data["price_history"], indent=2))

    except Exception as exc:
        print(f"Unexpected error: {exc}")

# import json
#
# import yfinance as yf
#
#
# def fetch_ticker_data() -> dict:
#     ticker = "AAPL"  # Hardcoded ticker input
#     stock = yf.Ticker(ticker)
#
#     history = stock.history(period="1mo")
#     history_json = history.reset_index().to_json(orient="records", date_format="iso")
#     return json.loads(history_json)
#
#
# if __name__ == "__main__":
#     try:
#         data = fetch_ticker_data()
#         print(json.dumps(data, indent=2))
#     except Exception as exc:
#         print(f"Unexpected error: {exc}")
