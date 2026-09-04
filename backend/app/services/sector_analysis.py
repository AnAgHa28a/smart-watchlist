"""Sector-relative move clustering.

A stock rarely moves in isolation. If four IT stocks all drop 2% on the same
day, that's a sector-wide (often market-wide) move — each individual stock
is not really "news" on its own. If one stock moves alone while its sector
peers are flat, that's genuinely idiosyncratic and worth a closer look. Most
DIY watchlists only ever show the raw number; this reclassifies it using
same-day peer behavior.
"""
from dataclasses import dataclass


@dataclass
class SectorClassification:
    label: str | None  # "sector-wide" | "idiosyncratic" | None
    sector_avg_move_pct: float | None
    peer_count: int


def compute_sector_avg_moves(symbol_changes: dict[str, float], symbol_sectors: dict[str, str]) -> dict[str, tuple[float, int]]:
    """symbol_changes: {symbol: change_pct}. Returns {sector: (avg_move_pct, count)}."""
    buckets: dict[str, list[float]] = {}
    for symbol, change_pct in symbol_changes.items():
        sector = symbol_sectors.get(symbol)
        if sector is None or change_pct is None:
            continue
        buckets.setdefault(sector, []).append(change_pct)

    return {
        sector: (sum(moves) / len(moves), len(moves))
        for sector, moves in buckets.items()
    }


def classify_sector_relative(
    change_pct: float | None,
    sector: str | None,
    sector_avg_moves: dict[str, tuple[float, int]],
) -> SectorClassification:
    if change_pct is None or sector is None or sector not in sector_avg_moves:
        return SectorClassification(label=None, sector_avg_move_pct=None, peer_count=0)

    sector_avg, peer_count = sector_avg_moves[sector]
    if peer_count < 3:  # need enough peers for the comparison to mean anything
        return SectorClassification(label=None, sector_avg_move_pct=sector_avg, peer_count=peer_count)

    same_direction = (change_pct >= 0) == (sector_avg >= 0)
    explained_fraction = 0.0
    if abs(change_pct) > 0.01 and same_direction:
        explained_fraction = min(abs(sector_avg) / abs(change_pct), 1.0)

    label = "sector-wide" if (same_direction and explained_fraction >= 0.5) else "idiosyncratic"
    return SectorClassification(label=label, sector_avg_move_pct=round(sector_avg, 2), peer_count=peer_count)
