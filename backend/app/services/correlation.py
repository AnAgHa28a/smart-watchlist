"""Detects watchlist concentration that static sector labels miss.

The sector-allocation widget catches "80% of your list is IT." It can't
catch two stocks in *different* sectors that still move together almost
every day (a bank and an NBFC, an exporter and its key supplier). This
computes real pairwise correlation of daily returns from each symbol's
own trailing close history — already stored for the sparkline, so this is
pure computation, no new data.
"""
import math
from dataclasses import dataclass

MIN_OVERLAP_DAYS = 20
CORRELATION_THRESHOLD = 0.7


@dataclass
class CorrelatedPair:
    symbol_a: str
    symbol_b: str
    correlation: float
    same_sector: bool


def _returns(closes: list[float]) -> list[float]:
    return [
        (closes[i] - closes[i - 1]) / closes[i - 1]
        for i in range(1, len(closes))
        if closes[i - 1]
    ]


def _pearson(a: list[float], b: list[float]) -> float | None:
    n = min(len(a), len(b))
    if n < MIN_OVERLAP_DAYS:
        return None
    a, b = a[-n:], b[-n:]
    mean_a, mean_b = sum(a) / n, sum(b) / n
    cov = sum((a[i] - mean_a) * (b[i] - mean_b) for i in range(n))
    var_a = sum((x - mean_a) ** 2 for x in a)
    var_b = sum((x - mean_b) ** 2 for x in b)
    denom = math.sqrt(var_a * var_b)
    return cov / denom if denom > 0 else None


def find_correlated_pairs(
    symbol_closes: dict[str, list[float]], symbol_sectors: dict[str, str | None],
) -> list[CorrelatedPair]:
    symbols = list(symbol_closes.keys())
    returns = {s: _returns(symbol_closes[s]) for s in symbols}

    pairs: list[CorrelatedPair] = []
    for i in range(len(symbols)):
        for j in range(i + 1, len(symbols)):
            a, b = symbols[i], symbols[j]
            r = _pearson(returns[a], returns[b])
            if r is None or abs(r) < CORRELATION_THRESHOLD:
                continue
            pairs.append(CorrelatedPair(
                symbol_a=a, symbol_b=b, correlation=round(r, 2),
                same_sector=symbol_sectors.get(a) == symbol_sectors.get(b),
            ))

    # Cross-sector pairs are the actual discovery (same-sector correlation is
    # already explained by the sector-allocation widget) — surface those first.
    pairs.sort(key=lambda p: (p.same_sector, -abs(p.correlation)))
    return pairs
