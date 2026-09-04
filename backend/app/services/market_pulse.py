"""Market Pulse: context beyond the user's own watchlist.

A personal watchlist only ever answers "how are MY stocks doing" — it can't
tell you whether today's IT selloff is a MY-stocks problem or a whole-market
problem. Since the poller already tracks the full ~80-symbol NSE universe
(not just symbols someone has watchlisted — see poller.py), this is free to
compute: aggregate today's moves across every tracked sector and surface the
handful that actually moved.
"""
from sqlalchemy.orm import Session

from app.models import PriceSnapshot, SymbolStats
from app.services.poller import load_universe
from app.services.attention_score import compute_attention_score, meaningful_for_tier
from app.services.market_hours import is_market_open
from app.schemas import MarketPulseResponse, SectorPulse, TopMover
from datetime import datetime


async def build_market_pulse(db: Session) -> MarketPulseResponse:
    universe = load_universe()
    snapshots = {row.symbol: row for row in db.query(PriceSnapshot).all()}
    stats_by_symbol = {row.symbol: row for row in db.query(SymbolStats).all()}

    sector_moves: dict[str, list[float]] = {}
    sector_flagged: dict[str, int] = {}
    movers: list[TopMover] = []
    flagged_count = 0

    for symbol, info in universe.items():
        snap = snapshots.get(symbol)
        if snap is None or not snap.prev_close:
            continue
        stats = stats_by_symbol.get(symbol)
        change_pct = (snap.price - snap.prev_close) / snap.prev_close * 100
        sector = info["sector"]
        sector_moves.setdefault(sector, []).append(change_pct)

        score_result = compute_attention_score(
            price=snap.price, prev_close=snap.prev_close, open_price=snap.open_price,
            volume=snap.volume,
            daily_return_stdev=stats.daily_return_stdev if stats else None,
            avg_volume_20d=stats.avg_volume_20d if stats else None,
            high_52w=stats.high_52w if stats else None,
            low_52w=stats.low_52w if stats else None,
            history_days=stats.history_days if stats else 0,
        )
        is_flagged = meaningful_for_tier(score_result.score, "trading")
        if is_flagged:
            flagged_count += 1
            sector_flagged[sector] = sector_flagged.get(sector, 0) + 1

        movers.append(TopMover(
            symbol=symbol, name=info["name"], sector=sector,
            change_pct=round(change_pct, 2), attention_score=score_result.score,
        ))

    sectors = [
        SectorPulse(
            sector=sector, avg_move_pct=round(sum(moves) / len(moves), 2),
            symbol_count=len(moves), flagged_count=sector_flagged.get(sector, 0),
        )
        for sector, moves in sector_moves.items()
    ]
    sectors.sort(key=lambda s: s.avg_move_pct)

    movers.sort(key=lambda m: -m.attention_score)

    return MarketPulseResponse(
        generated_at=datetime.utcnow(),
        market_open=is_market_open(),
        universe_size=len(universe),
        flagged_count=flagged_count,
        sectors=sectors,
        top_movers=movers[:6],
    )
