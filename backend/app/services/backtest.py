"""Replays the attention-score algorithm across a year of real historical
prices, day by day, using only data available as of each simulated day (no
lookahead — the trailing stdev/volume/52w-high-low windows for day i only
ever look at days before i) — so the product can show a real, immediately
populated track record instead of an empty promise on day one. The same
function (compute_attention_score) that scores live data scores historical
data here, so the backtest and the live product are guaranteed consistent —
this isn't a separate approximation of the algorithm, it's the algorithm.

Also produces the trailing score series used for the score-trend sparkline,
since it's a free byproduct of the same walk.
"""
from datetime import datetime, date

from app.services.attention_score import compute_attention_score, meaningful_for_tier, compute_daily_return_stdev

STDEV_WINDOW = 60
VOLUME_WINDOW = 20
LEVEL_WINDOW = 252
FORWARD_DAYS = 5          # trading sessions ahead to grade a flag against
FLAT_THRESHOLD_PCT = 0.3  # forward moves smaller than this count as "flat"
MIN_WINDOW = 30           # minimum trailing days before a day is scored at all


def simulate_symbol(
    timestamps: list[int], closes: list[float], opens: list[float | None], volumes: list[float | None],
) -> tuple[list[float], list[dict]]:
    """Returns (recent_scores, flag_events). flag_events are plain dicts,
    already graded — since this is historical data, the 'future' needed to
    grade each flag is already in hand."""
    n = len(closes)
    scores: list[float] = []
    flags: list[dict] = []

    for i in range(MIN_WINDOW, n):
        window_closes = closes[max(0, i - STDEV_WINDOW):i]
        window_volumes = [v for v in volumes[max(0, i - VOLUME_WINDOW):i] if v is not None]
        level_closes = closes[max(0, i - LEVEL_WINDOW):i]

        stdev = compute_daily_return_stdev(window_closes)
        avg_volume = sum(window_volumes) / len(window_volumes) if window_volumes else None
        high_52w = max(level_closes) if level_closes else None
        low_52w = min(level_closes) if level_closes else None

        price = closes[i]
        prev_close = closes[i - 1]
        open_price = opens[i] if i < len(opens) else None
        volume = volumes[i] if i < len(volumes) else None

        result = compute_attention_score(
            price=price, prev_close=prev_close, open_price=open_price, volume=volume,
            daily_return_stdev=stdev, avg_volume_20d=avg_volume,
            high_52w=high_52w, low_52w=low_52w,
            history_days=len(window_closes),
        )
        scores.append(result.score)

        if not meaningful_for_tier(result.score, "trading"):
            continue
        if i + FORWARD_DAYS >= n:
            continue  # not enough future data yet to grade this one

        today_return = (price - prev_close) / prev_close * 100 if prev_close else 0.0
        direction = 1 if today_return >= 0 else -1

        forward_price = closes[i + FORWARD_DAYS]
        forward_return = (forward_price - price) / price * 100 if price else 0.0
        forward_direction = 1 if forward_return >= 0 else -1

        if abs(forward_return) < FLAT_THRESHOLD_PCT:
            outcome = "flat"
        elif direction == forward_direction:
            outcome = "continued"
        else:
            outcome = "reverted"

        event_date = datetime.utcfromtimestamp(timestamps[i]).date() if i < len(timestamps) else date.today()
        flags.append({
            "event_date": event_date,
            "score": result.score,
            "price_at_flag": price,
            "move_direction": direction,
            "outcome": outcome,
            "forward_return_pct": round(forward_return, 2),
        })

    return scores[-60:], flags
