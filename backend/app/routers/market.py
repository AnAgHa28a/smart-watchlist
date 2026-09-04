from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import MarketPulseResponse
from app.auth import get_current_user
from app.services.market_pulse import build_market_pulse

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/pulse", response_model=MarketPulseResponse)
async def get_market_pulse(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Universe-wide context, independent of any one user's watchlist —
    which sectors are actually moving today, and how much of the tracked
    market is flagged as unusual right now."""
    return await build_market_pulse(db)
