from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import FlagEvent
from app.schemas import TrackRecordResponse, TrackRecordBucket


def build_track_record(db: Session) -> TrackRecordResponse:
    graded = db.query(FlagEvent).filter(FlagEvent.graded.is_(True)).all()

    total = len(graded)
    continued = sum(1 for e in graded if e.outcome == "continued")
    reverted = sum(1 for e in graded if e.outcome == "reverted")
    flat = sum(1 for e in graded if e.outcome == "flat")

    backtest_count = sum(1 for e in graded if e.source == "backtest")
    live_count = sum(1 for e in graded if e.source == "live")
    live_pending = db.query(func.count(FlagEvent.id)).filter(
        FlagEvent.source == "live", FlagEvent.graded.is_(False)
    ).scalar() or 0

    def pct(n: int) -> float:
        return round(n / total * 100, 1) if total else 0.0

    # Bucket by score magnitude — does a higher score actually correlate
    # with a higher continuation rate? If it didn't, that would be a sign
    # the algorithm's weighting needs work; showing it either way is the
    # honest move.
    buckets_def = [("30-50", 30, 50), ("50-70", 50, 70), ("70-100", 70, 101)]
    buckets = []
    for label, lo, hi in buckets_def:
        subset = [e for e in graded if lo <= e.score < hi]
        n = len(subset)
        cont = sum(1 for e in subset if e.outcome == "continued")
        buckets.append(TrackRecordBucket(
            label=label, count=n,
            continued_pct=round(cont / n * 100, 1) if n else 0.0,
        ))

    return TrackRecordResponse(
        total_graded=total,
        continued_pct=pct(continued),
        reverted_pct=pct(reverted),
        flat_pct=pct(flat),
        backtest_count=backtest_count,
        live_count=live_count,
        live_pending=live_pending,
        buckets=buckets,
    )
