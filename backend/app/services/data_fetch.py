"""Multi-source price fetching with a graceful cascade + fallback.

Reality check done during build: NSE's own site (nseindia.com) returns 403
even with a proper browser User-Agent — its bot-detection (Akamai) blocks
non-browser clients outright, and this is *worse* from a cloud host's IP
range than from a residential one. There is no free, reliable, real-time
NSE-direct source. So the design cascades instead of betting on one:

  1. NSE's own live quote endpoint — kept as a best-effort first attempt
     (would be lowest latency if it ever succeeds), circuit-broken so a
     failing run doesn't get hammered every poll tick.
  2. Yahoo Finance's public chart JSON endpoint, called directly over HTTPS
     (not through the `yfinance` package — verified during build that a
     plain httpx GET with a browser User-Agent returns clean data; going
     direct avoids an extra dependency's own fragility/breakage risk).
     This is the real backbone of the system.
  3. Last known-good value from our own DB cache, marked stale.

The same Yahoo endpoint, called with range=1y, also backfills a full year of
daily OHLCV per symbol in one shot — this is what seeds the statistical
baseline (volatility, 52w high/low, average volume) instead of depending on
NSE's Bhavcopy archives, which are equally unreachable in practice.
"""
import asyncio
import logging
import time

import httpx

from app.services.circuit_breaker import data_source_breaker

logger = logging.getLogger("data_fetch")

NSE_BASE = "https://www.nseindia.com"
YAHOO_CHART = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
}

_YAHOO_CONCURRENCY = asyncio.Semaphore(5)


async def fetch_nse_live_batch(symbols: list[str]) -> dict[str, dict]:
    """Best-effort direct-from-exchange quotes. Expected to fail often (or
    always, from most cloud hosts) — that's a documented, accepted tradeoff,
    not a bug: it's a bonus fast-path, not the backbone."""
    if data_source_breaker.is_open("nse_live"):
        return {}

    results: dict[str, dict] = {}
    try:
        async with httpx.AsyncClient(headers=BROWSER_HEADERS, timeout=4.0, follow_redirects=True) as client:
            await client.get(NSE_BASE)  # mint session cookies
            for symbol in symbols:
                try:
                    resp = await client.get(f"{NSE_BASE}/api/quote-equity", params={"symbol": symbol})
                    if resp.status_code != 200:
                        continue
                    data = resp.json()
                    price_info = data.get("priceInfo", {})
                    last_price = price_info.get("lastPrice")
                    if last_price is None:
                        continue
                    results[symbol] = {
                        "price": float(last_price),
                        "prev_close": float(price_info.get("previousClose") or 0) or None,
                        "open": float(price_info.get("open") or 0) or None,
                        "volume": None,
                        "source": "nse_live",
                    }
                except Exception:
                    continue
        if results:
            data_source_breaker.record_success("nse_live")
        else:
            data_source_breaker.record_failure("nse_live")
    except Exception as e:
        logger.info(f"NSE live batch unavailable (expected on most hosts): {e}")
        data_source_breaker.record_failure("nse_live")

    return results


async def _fetch_one_yahoo(client: httpx.AsyncClient, symbol: str, range_: str, interval: str) -> tuple[str, dict | None]:
    async with _YAHOO_CONCURRENCY:
        try:
            resp = await client.get(
                YAHOO_CHART.format(symbol=f"{symbol}.NS"),
                params={"interval": interval, "range": range_},
            )
            if resp.status_code != 200:
                return symbol, None
            data = resp.json()
            result = data.get("chart", {}).get("result")
            if not result:
                return symbol, None
            return symbol, result[0]
        except Exception:
            return symbol, None


async def fetch_yahoo_live_batch(symbols: list[str]) -> dict[str, dict]:
    if not symbols or data_source_breaker.is_open("yahoo"):
        return {}

    results: dict[str, dict] = {}
    try:
        async with httpx.AsyncClient(headers=BROWSER_HEADERS, timeout=6.0) as client:
            tasks = [_fetch_one_yahoo(client, s, "1d", "1d") for s in symbols]
            for symbol, chart_result in await asyncio.gather(*tasks):
                if chart_result is None:
                    continue
                meta = chart_result.get("meta", {})
                price = meta.get("regularMarketPrice")
                if price is None:
                    continue
                results[symbol] = {
                    "price": float(price),
                    "prev_close": float(meta.get("previousClose") or meta.get("chartPreviousClose") or 0) or None,
                    "open": None,
                    "volume": float(meta.get("regularMarketVolume") or 0) or None,
                    "source": "yahoo",
                }
        if results:
            data_source_breaker.record_success("yahoo")
        else:
            data_source_breaker.record_failure("yahoo")
    except Exception as e:
        logger.warning(f"Yahoo batch fetch failed entirely: {e}")
        data_source_breaker.record_failure("yahoo")

    return results


async def fetch_prices(symbols: list[str]) -> dict[str, dict]:
    """Cascade across sources for a batch of symbols. Returns whatever it
    could get; the caller (poller) falls back to the DB cache for symbols
    missing from the result and marks them stale."""
    if not symbols:
        return {}

    merged: dict[str, dict] = {}

    nse_results = await fetch_nse_live_batch(symbols)
    merged.update(nse_results)

    remaining = [s for s in symbols if s not in merged]
    if remaining:
        yahoo_results = await fetch_yahoo_live_batch(remaining)
        merged.update(yahoo_results)

    return merged


async def fetch_historical(symbol: str) -> dict | None:
    """One year of daily OHLCV for a single symbol — used to seed/refresh
    the statistical baseline (volatility, 52w high/low, avg volume) and, via
    services/backtest.py, to replay the algorithm day-by-day for the
    self-graded track record. All four series are kept positionally aligned
    by index (day i's close/open/volume/timestamp) — a previous version
    filtered volume nulls independently of closes, which could desync the
    arrays; here a missing open/volume becomes None in place rather than
    being dropped, so index i always means the same trading day everywhere."""
    try:
        async with httpx.AsyncClient(headers=BROWSER_HEADERS, timeout=8.0) as client:
            _, chart_result = await _fetch_one_yahoo(client, symbol, "1y", "1d")
    except Exception:
        return None

    if chart_result is None:
        return None

    try:
        timestamps = chart_result.get("timestamp", [])
        quote = chart_result["indicators"]["quote"][0]
        closes = quote.get("close", [])
        volumes = quote.get("volume", [])
        opens = quote.get("open", [])
        meta = chart_result.get("meta", {})

        rows = [
            (ts, c, o, v) for ts, c, o, v in zip(timestamps, closes, opens, volumes)
            if c is not None
        ]
        if len(rows) < 2:
            return None

        return {
            "timestamps": [r[0] for r in rows],
            "closes": [r[1] for r in rows],
            "opens": [r[2] for r in rows],
            "volumes": [r[3] for r in rows],
            "high_52w": meta.get("fiftyTwoWeekHigh"),
            "low_52w": meta.get("fiftyTwoWeekLow"),
            "fetched_at": time.time(),
        }
    except (KeyError, IndexError, TypeError):
        return None
