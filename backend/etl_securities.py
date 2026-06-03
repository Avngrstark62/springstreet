from db import database
from logger import get_logger, log_error
from yf_service import fetch_security_data

logger = get_logger(__name__)


def run() -> None:
    session_gen = database.session()
    db = next(session_gen)

    try:
        tickers = database.get_unique_holding_tickers(db)
        if not tickers:
            logger.info("No holdings found. Nothing to sync for securities.")
            return

        logger.info("Found %s unique tickers from holdings", len(tickers))
        security_records: list[dict] = []
        for ticker in tickers:
            try:
                security_records.append(fetch_security_data(ticker))
            except Exception as exc:
                log_error(logger, f"Failed to fetch security metadata for {ticker}", exc)

        if not security_records:
            logger.info("No security records fetched. Nothing to upsert.")
            return

        synced = database.bulk_upsert_securities(db, security_records)
        logger.info("Securities sync completed. Upserted %s rows", synced)
    except Exception as exc:
        db.rollback()
        log_error(logger, "Securities sync failed", exc)
    finally:
        session_gen.close()


if __name__ == "__main__":
    run()
