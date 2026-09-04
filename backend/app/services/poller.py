"""The single server-side poller.

This is the scaling answer to the brief's 'how does this scale to more
users and larger watchlists' question: there is exactly one poller, tracking
the fixed ~80-symbol NSE universe (app/data/nifty_universe.json), regardless
of how many users or watchlists exist. Cost is O(universe size), not O(users
x watchlist size) — adding the 10,000th user adds zero additional upstream
API calls. Every client reads from the shared price_snapshots cache table
instead of triggering its own fetch.
"""
import asyncio
import json
import logging
import os
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import PriceSnapshot, SymbolStats, DataSource
from app.services.data_fetch import fetch_prices, fetch_historical
from app.services.attention_score import compute_daily_return_stdev
from app.services.market_hours import is_market_open
from app.config import settings

logger = logging.getLogger("poller")

_UNIVERSE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "nifty_universe.json")

_universe_cache: dict[str, dict] | None = None


def load_universe() -> dict[str, dict]:
    global _universe_cache
    if _universe_cache is None:
        with open(_UNIVERSE_PATH) as f:
            _universe_cache = json.load(f)
    return _universe_cache


async def backfill_symbol_stats(db: Session, symbol: str, sector: str, name: str) -> None:
    hist = await fetch_historical(symbol)
    if hist is None:
        logger.info(f"Historical backfill unavailable for {symbol}; will retry next cycle")
        return

    closes = hist["closes"]
    volumes = hist["volumes"]
    stdev = compute_daily_return_stdev(closes)
    avg_volume = sum(volumes) / len(volumes) if volumes else None
    high_52w = hist.get("high_52w") or max(closes)
    low_52w = hist.get("low_52w") or min(closes)

    row = db.get(SymbolStats, symbol)
    if row is None:
        row = SymbolStats(symbol=symbol)
        db.add(row)
    row.daily_return_stdev = stdev
    row.avg_volume_20d = avg_volume
    row.high_52w = high_52w
    row.low_52w = low_52w
    row.history_days = len(closes)
    row.sector = sector
    row.name = name
    row.recent_closes = closes[-60:]
    row.last_updated = datetime.utcnow()
    db.commit()


async def run_backfill_pass(stale_after_hours: int = 20) -> None:
    universe = load_universe()
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(hours=stale_after_hours)
        for symbol, info in universe.items():
            existing = db.get(SymbolStats, symbol)
            if existing and existing.last_updated and existing.last_updated > cutoff and existing.daily_return_stdev:
                continue
            await backfill_symbol_stats(db, symbol, info["sector"], info["name"])
            await asyncio.sleep(0.15)  # be a polite citizen to the upstream API
    finally:
        db.close()


async def poll_once() -> None:
    universe = load_universe()
    symbols = list(universe.keys())
    db = SessionLocal()
    try:
        fetched = await fetch_prices(symbols)
        now = datetime.utcnow()

        for symbol in symbols:
            data = fetched.get(symbol)
            row = db.get(PriceSnapshot, symbol)

            if data is not None:
                if row is None:
                    row = PriceSnapshot(symbol=symbol)
                    db.add(row)
                row.price = data["price"]
                row.volume = data.get("volume")
                row.prev_close = data.get("prev_close")
                row.open_price = data.get("open")
                row.source = DataSource(data["source"])
                row.is_stale = False
                row.fetched_at = now
            elif row is not None:
                # No fresh data from any source this cycle — keep the last
                # known-good value but flag it stale rather than erroring.
                row.is_stale = True
            # else: never had data for this symbol yet; nothing to show,
            # will pick it up as soon as any source succeeds.

        db.commit()
    except Exception as e:
        logger.error(f"Poll cycle failed: {e}")
        db.rollback()
    finally:
        db.close()


async def poller_loop(stop_event: asyncio.Event) -> None:
    await run_backfill_pass()
    while not stop_event.is_set():
        try:
            await poll_once()
        except Exception as e:
            logger.error(f"Unhandled error in poll cycle: {e}")

        interval = (
            settings.poll_interval_market_open_seconds
            if is_market_open()
            else settings.poll_interval_market_closed_seconds
        )
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval)
        except asyncio.TimeoutError:
            pass

        # Refresh statistical baselines once a day, off the hot path.
        if datetime.utcnow().hour == 2 and datetime.utcnow().minute < 5:
            await run_backfill_pass()
