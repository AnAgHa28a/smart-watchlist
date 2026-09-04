from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, WatchlistItem, ConvictionTier
from app.schemas import (
    AddSymbolRequest, UpdateTierRequest, WatchlistResponse, SymbolSearchResult,
)
from app.auth import get_current_user
from app.services.watchlist_service import build_watchlist_response
from app.services.poller import load_universe

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


@router.get("", response_model=WatchlistResponse)
async def get_watchlist(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """A 'visit' — diffs against and advances last-seen checkpoints, computes
    the digest. Call on page load and when the tab regains focus."""
    return await build_watchlist_response(db, user.id, touch_checkpoints=True)


@router.get("/live", response_model=WatchlistResponse)
async def get_watchlist_live(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Passive refresh for background polling — current prices/scores only,
    never advances checkpoints. Keeps numbers ticking without the digest
    silently collapsing to empty a few seconds after the real visit."""
    return await build_watchlist_response(db, user.id, touch_checkpoints=False)


@router.get("/search", response_model=list[SymbolSearchResult])
def search_symbols(q: str = "", user: User = Depends(get_current_user)):
    universe = load_universe()
    q_upper = q.strip().upper()
    if not q_upper:
        results = list(universe.items())[:20]
    else:
        results = [
            (s, info) for s, info in universe.items()
            if q_upper in s or q_upper in info["name"].upper()
        ][:20]
    return [SymbolSearchResult(symbol=s, name=info["name"], sector=info["sector"]) for s, info in results]


@router.post("/items", status_code=status.HTTP_201_CREATED)
def add_symbol(payload: AddSymbolRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    universe = load_universe()
    symbol = payload.symbol.strip().upper()
    if symbol not in universe:
        raise HTTPException(status_code=400, detail=f"Unknown symbol '{symbol}' — not in the tracked NSE universe")

    if payload.conviction_tier not in (ConvictionTier.core.value, ConvictionTier.trading.value):
        raise HTTPException(status_code=400, detail="conviction_tier must be 'core' or 'trading'")

    existing = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == user.id, WatchlistItem.symbol == symbol
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"{symbol} is already on your watchlist")

    item = WatchlistItem(user_id=user.id, symbol=symbol, conviction_tier=ConvictionTier(payload.conviction_tier))
    db.add(item)
    db.commit()
    return {"ok": True, "symbol": symbol}


@router.delete("/items/{symbol}")
def remove_symbol(symbol: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    symbol = symbol.strip().upper()
    item = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == user.id, WatchlistItem.symbol == symbol
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Symbol not on watchlist")
    db.delete(item)
    db.commit()
    return {"ok": True}


@router.patch("/items/{symbol}")
def update_tier(symbol: str, payload: UpdateTierRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    symbol = symbol.strip().upper()
    if payload.conviction_tier not in (ConvictionTier.core.value, ConvictionTier.trading.value):
        raise HTTPException(status_code=400, detail="conviction_tier must be 'core' or 'trading'")

    item = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == user.id, WatchlistItem.symbol == symbol
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Symbol not on watchlist")

    item.conviction_tier = ConvictionTier(payload.conviction_tier)
    db.commit()
    return {"ok": True}
