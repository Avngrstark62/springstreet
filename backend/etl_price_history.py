from db import database
from logger import get_logger, log_error
from yf_service import fetch_price_history_for_tickers

logger = get_logger(__name__)


def run() -> None:
    session_gen = database.session()
    db = next(session_gen)

    try:
        tickers = database.get_unique_holding_tickers(db)
        if not tickers:
            logger.info("No holdings found. Nothing to sync for price history.")
            return

        logger.info("Found %s unique tickers from holdings", len(tickers))
        price_history_by_ticker = fetch_price_history_for_tickers(
            tickers,
            range_period="1y",
            interval="1d",
        )
        price_history_records = [
            {
                "ticker": ticker,
                "date": row["date"],
                "open_price": row.get("open_price"),
                "high_price": row.get("high_price"),
                "low_price": row.get("low_price"),
                "close_price": row.get("close_price"),
                "volume": row.get("volume"),
            }
            for ticker, rows in price_history_by_ticker.items()
            for row in rows
        ]
        total_rows = database.bulk_upsert_price_history(db, price_history_records)
        logger.info("Price history sync completed. Upserted %s rows", total_rows)
    except Exception as exc:
        db.rollback()
        log_error(logger, "Price history sync failed", exc)
    finally:
        session_gen.close()


if __name__ == "__main__":
    run()
