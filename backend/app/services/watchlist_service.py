from datetime import datetime

from sqlalchemy.orm import Session

from app.models import WatchlistItem, PriceSnapshot, SymbolStats, UserSymbolCheckpoint
from app.services.attention_score import compute_attention_score, meaningful_for_tier
from app.services.sector_analysis import compute_sector_avg_moves, classify_sector_relative
from app.services.market_hours import is_market_open
from app.services.poller import load_universe
from app.services.digest import generate_digest_narrative
from app.schemas import WatchlistEntryOut, SignalBreakdown, DigestItem, WatchlistResponse

# How much the score (or price) must move beyond what the user already saw
# before we re-flag an already-acknowledged symbol in the digest again.
SCORE_DELTA_REFLAG = 8.0
PRICE_DELTA_REFLAG_PCT = 1.0


async def build_watchlist_response(db: Session, user_id: int, touch_checkpoints: bool = True) -> WatchlistResponse:
    """touch_checkpoints=True is a 'visit': it diffs against and then advances
    the user's last-seen checkpoints, and computes the digest. Used on page
    load and when the tab regains focus after being away.

    touch_checkpoints=False is a passive live refresh: current prices/scores
    only, no checkpoint mutation, no digest recompute. Used for the frequent
    background poll that keeps numbers ticking while the user is actively
    looking at the page — without that split, a naive fixed-interval poll
    would silently mark everything 'seen' every few seconds and the digest
    would collapse to empty almost immediately after load."""
    universe = load_universe()

    # Sector-relative context is computed across the FULL tracked universe,
    # not just this user's list, so it's statistically meaningful even for
    # a watchlist with only one or two stocks in a given sector.
    all_snapshots = {row.symbol: row for row in db.query(PriceSnapshot).all()}
    universe_changes = {}
    for symbol, snap in all_snapshots.items():
        if snap.prev_close:
            universe_changes[symbol] = (snap.price - snap.prev_close) / snap.prev_close * 100
    symbol_sectors = {s: info["sector"] for s, info in universe.items()}
    sector_avg_moves = compute_sector_avg_moves(universe_changes, symbol_sectors)

    items_db = db.query(WatchlistItem).filter(WatchlistItem.user_id == user_id).all()
    symbols = [i.symbol for i in items_db]

    stats_by_symbol = {
        row.symbol: row for row in db.query(SymbolStats).filter(SymbolStats.symbol.in_(symbols)).all()
    } if symbols else {}
    checkpoints_by_symbol = {
        row.symbol: row for row in db.query(UserSymbolCheckpoint)
        .filter(UserSymbolCheckpoint.user_id == user_id, UserSymbolCheckpoint.symbol.in_(symbols)).all()
    } if symbols else {}

    market_open = is_market_open()
    now = datetime.utcnow()
    results: list[WatchlistEntryOut] = []
    digest_candidates: list[tuple[float, WatchlistEntryOut, dict]] = []

    for item in items_db:
        snap = all_snapshots.get(item.symbol)
        stats = stats_by_symbol.get(item.symbol)
        checkpoint = checkpoints_by_symbol.get(item.symbol)
        universe_info = universe.get(item.symbol, {})

        if snap is None:
            # Never fetched yet (e.g. just added, poller hasn't run) — distinct
            # from "stale", which means we HAD live data and it's since gone
            # stale. The frontend only shows the stale badge once a price exists.
            results.append(WatchlistEntryOut(
                symbol=item.symbol, name=universe_info.get("name"), sector=universe_info.get("sector"),
                conviction_tier=item.conviction_tier.value, is_stale=False,
                insufficient_history=True,
            ))
            continue

        change_pct = ((snap.price - snap.prev_close) / snap.prev_close * 100) if snap.prev_close else None

        score_result = compute_attention_score(
            price=snap.price, prev_close=snap.prev_close, open_price=snap.open_price,
            volume=snap.volume,
            daily_return_stdev=stats.daily_return_stdev if stats else None,
            avg_volume_20d=stats.avg_volume_20d if stats else None,
            high_52w=stats.high_52w if stats else None,
            low_52w=stats.low_52w if stats else None,
            history_days=stats.history_days if stats else 0,
        )

        sector_cls = classify_sector_relative(change_pct, universe_info.get("sector"), sector_avg_moves)

        is_new = checkpoint is None
        price_delta = (snap.price - checkpoint.last_seen_price) if (checkpoint and checkpoint.last_seen_price) else None
        price_delta_pct = (price_delta / checkpoint.last_seen_price * 100) if (price_delta and checkpoint.last_seen_price) else None
        score_delta = (score_result.score - checkpoint.last_seen_attention_score) if (checkpoint and checkpoint.last_seen_attention_score is not None) else None

        entry = WatchlistEntryOut(
            symbol=item.symbol,
            name=stats.name if stats and stats.name else universe_info.get("name"),
            sector=universe_info.get("sector"),
            conviction_tier=item.conviction_tier.value,
            price=snap.price,
            prev_close=snap.prev_close,
            change_pct=round(change_pct, 2) if change_pct is not None else None,
            volume=snap.volume,
            is_stale=snap.is_stale,
            source=snap.source.value,
            fetched_at=snap.fetched_at,
            attention_score=score_result.score,
            signals=SignalBreakdown(
                z_score=score_result.z_score,
                volume_ratio=score_result.volume_ratio,
                near_52w_high=score_result.near_52w_high,
                near_52w_low=score_result.near_52w_low,
                gap_pct=score_result.gap_pct,
                sector_relative=sector_cls.label,
                sector_avg_move_pct=sector_cls.sector_avg_move_pct,
                explanation=score_result.explanation,
            ),
            is_new_since_last_visit=is_new,
            price_change_since_last_seen=round(price_delta, 2) if price_delta is not None else None,
            price_change_pct_since_last_seen=round(price_delta_pct, 2) if price_delta_pct is not None else None,
            score_delta_since_last_seen=round(score_delta, 1) if score_delta is not None else None,
            last_seen_at=checkpoint.last_seen_at if checkpoint else None,
            insufficient_history=score_result.insufficient_history,
        )
        results.append(entry)

        is_meaningful_now = meaningful_for_tier(score_result.score, item.conviction_tier.value)
        should_flag = is_meaningful_now and (
            is_new
            or (score_delta is not None and score_delta >= SCORE_DELTA_REFLAG)
            or (price_delta_pct is not None and abs(price_delta_pct) >= PRICE_DELTA_REFLAG_PCT)
        )
        if should_flag:
            digest_candidates.append((score_result.score, entry, {
                "symbol": item.symbol,
                "explanation": score_result.explanation,
                "sector_label": sector_cls.label,
            }))

        # Update the checkpoint now — the diff just computed is against the
        # OLD checkpoint; this write is what makes the next visit diff from
        # this moment on, from any device. Skipped entirely on a passive
        # live-refresh poll, so background polling can't silently advance
        # "last seen" — only an actual visit does.
        if touch_checkpoints:
            if checkpoint is None:
                checkpoint = UserSymbolCheckpoint(user_id=user_id, symbol=item.symbol)
                db.add(checkpoint)
            checkpoint.last_seen_at = now
            checkpoint.last_seen_price = snap.price
            checkpoint.last_seen_attention_score = score_result.score

    if touch_checkpoints:
        db.commit()

    results.sort(key=lambda e: (e.attention_score is None, -(e.attention_score or 0)))
    digest_candidates.sort(key=lambda t: -t[0])

    digest = [
        DigestItem(symbol=d["symbol"], headline=d["explanation"], attention_score=score, reason=d["explanation"])
        for score, _entry, d in digest_candidates[:8]
    ]
    narrative = await generate_digest_narrative(
        [{"symbol": d["symbol"], "explanation": d["explanation"], "sector_label": d["sector_label"]} for _, _, d in digest_candidates[:5]],
        total_count=len(items_db),
        market_open=market_open,
    )

    return WatchlistResponse(
        market_open=market_open,
        generated_at=now,
        digest=digest,
        digest_narrative=narrative,
        items=results,
    )
