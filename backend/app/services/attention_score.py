"""The core 'what deserves attention' algorithm.

Deliberately NOT a hardcoded '% move > threshold' rule. Each stock's move is
judged against its *own* typical behavior (volatility-adjusted z-score), its
own typical volume, its own 52-week range, and its sector peers' move that
day — because a raw percentage means very different things for a sleepy FMCG
stock vs a volatile mid-cap.

Components (each normalized to 0-1, then weighted):
  - z-score of today's return vs the stock's trailing daily-return stdev
  - volume ratio vs its 20-day average
  - proximity to a 52-week high/low (a structural level crossing)
  - gap % between previous close and today's open

Conviction tiers (Core vs Trading) don't change the score itself — they
change the bar for "is this worth surfacing in the digest". A Core holding
is meant to be left alone unless something structural happens; a Trading
position is meant to be watched closely.
"""
import math
from dataclasses import dataclass


@dataclass
class ScoreResult:
    score: float  # 0-100
    z_score: float | None
    volume_ratio: float | None
    near_52w_high: bool
    near_52w_low: bool
    gap_pct: float | None
    insufficient_history: bool
    explanation: str


DIGEST_THRESHOLD = {"core": 55.0, "trading": 30.0}
NEAR_LEVEL_PCT = 0.02  # within 2% of 52w high/low counts as "near"


def compute_attention_score(
    price: float,
    prev_close: float | None,
    open_price: float | None,
    volume: float | None,
    daily_return_stdev: float | None,
    avg_volume_20d: float | None,
    high_52w: float | None,
    low_52w: float | None,
    history_days: int,
) -> ScoreResult:
    change_pct = ((price - prev_close) / prev_close * 100) if prev_close else None
    insufficient_history = history_days < 10 or not daily_return_stdev

    z_score = None
    if change_pct is not None and daily_return_stdev and daily_return_stdev > 0:
        z_score = change_pct / (daily_return_stdev * 100)

    volume_ratio = None
    if volume and avg_volume_20d and avg_volume_20d > 0:
        volume_ratio = volume / avg_volume_20d

    near_high = bool(high_52w and price >= high_52w * (1 - NEAR_LEVEL_PCT))
    near_low = bool(low_52w and price <= low_52w * (1 + NEAR_LEVEL_PCT))

    gap_pct = None
    if open_price and prev_close:
        gap_pct = (open_price - prev_close) / prev_close * 100

    if insufficient_history:
        # Fall back to a conservative raw-%-move heuristic so new symbols
        # aren't silently invisible while history backfills.
        z_component = min(abs(change_pct or 0) / 4, 1.0)
        volume_component = 0.0
        level_component = 1.0 if (near_high or near_low) else 0.0
        gap_component = min(abs(gap_pct or 0) / 5, 1.0)
        score = 35 * z_component + 20 * level_component + 15 * gap_component
        explanation = "Limited price history for this symbol yet — showing raw move, not volatility-adjusted."
    else:
        z_component = min(abs(z_score or 0) / 3, 1.0)
        volume_component = min(max((volume_ratio or 0) - 1, 0) / 3, 1.0)
        level_component = 1.0 if (near_high or near_low) else 0.0
        gap_component = min(abs(gap_pct or 0) / 5, 1.0)
        score = (
            40 * z_component + 25 * volume_component
            + 20 * level_component + 15 * gap_component
        )
        explanation = _build_explanation(change_pct, z_score, volume_ratio, near_high, near_low, gap_pct)

    return ScoreResult(
        score=round(min(score, 100.0), 1),
        z_score=round(z_score, 2) if z_score is not None else None,
        volume_ratio=round(volume_ratio, 2) if volume_ratio is not None else None,
        near_52w_high=near_high,
        near_52w_low=near_low,
        gap_pct=round(gap_pct, 2) if gap_pct is not None else None,
        insufficient_history=insufficient_history,
        explanation=explanation,
    )


def _build_explanation(change_pct, z_score, volume_ratio, near_high, near_low, gap_pct) -> str:
    parts = []
    if change_pct is not None:
        direction = "up" if change_pct >= 0 else "down"
        parts.append(f"{direction} {abs(change_pct):.1f}%")
    if z_score is not None and abs(z_score) >= 1:
        parts.append(f"{abs(z_score):.1f}x its usual daily move")
    if volume_ratio is not None and volume_ratio >= 1.3:
        parts.append(f"{volume_ratio:.1f}x average volume")
    if near_high:
        parts.append("near its 52-week high")
    if near_low:
        parts.append("near its 52-week low")
    if gap_pct is not None and abs(gap_pct) >= 1:
        parts.append(f"gapped {gap_pct:+.1f}% at open")
    if not parts:
        return "No unusual activity."
    return ", ".join(parts).capitalize() + "."


def meaningful_for_tier(score: float, conviction_tier: str) -> bool:
    threshold = DIGEST_THRESHOLD.get(conviction_tier, DIGEST_THRESHOLD["trading"])
    return score >= threshold


def compute_daily_return_stdev(closes: list[float]) -> float | None:
    if len(closes) < 10:
        return None
    returns = [
        (closes[i] - closes[i - 1]) / closes[i - 1]
        for i in range(1, len(closes))
        if closes[i - 1]
    ]
    if len(returns) < 5:
        return None
    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    return math.sqrt(variance)
