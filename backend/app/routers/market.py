from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import MarketPulseResponse, TrackRecordResponse
from app.auth import get_current_user
from app.services.market_pulse import build_market_pulse
from app.services.track_record import build_track_record

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/pulse", response_model=MarketPulseResponse)
async def get_market_pulse(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Universe-wide context, independent of any one user's watchlist —
    which sectors are actually moving today, and how much of the tracked
    market is flagged as unusual right now."""
    return await build_market_pulse(db)


@router.get("/track-record", response_model=TrackRecordResponse)
def get_track_record(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """The algorithm's own honest scorecard: of everything it has ever
    flagged as meaningful (a year of backtested history, plus live flags as
    they mature), how often did the move actually continue vs revert."""
    return build_track_record(db)
