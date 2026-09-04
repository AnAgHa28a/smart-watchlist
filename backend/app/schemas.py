from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


# --- Auth ---
class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str

    class Config:
        from_attributes = True


# --- Watchlist ---
class AddSymbolRequest(BaseModel):
    symbol: str
    conviction_tier: str = "trading"


class UpdateTierRequest(BaseModel):
    conviction_tier: str


class SignalBreakdown(BaseModel):
    z_score: float | None = None
    volume_ratio: float | None = None
    near_52w_high: bool = False
    near_52w_low: bool = False
    gap_pct: float | None = None
    sector_relative: str | None = None  # "sector-wide" | "idiosyncratic" | None
    sector_avg_move_pct: float | None = None
    explanation: str = ""


class WatchlistEntryOut(BaseModel):
    symbol: str
    name: str | None = None
    sector: str | None = None
    conviction_tier: str
    price: float | None = None
    prev_close: float | None = None
    change_pct: float | None = None
    volume: float | None = None
    is_stale: bool = False
    source: str | None = None
    fetched_at: datetime | None = None
    attention_score: float | None = None
    signals: SignalBreakdown | None = None

    # diff-since-last-seen
    is_new_since_last_visit: bool = False
    price_change_since_last_seen: float | None = None
    price_change_pct_since_last_seen: float | None = None
    score_delta_since_last_seen: float | None = None
    last_seen_at: datetime | None = None
    insufficient_history: bool = False


class DigestItem(BaseModel):
    symbol: str
    headline: str
    attention_score: float
    reason: str


class WatchlistResponse(BaseModel):
    market_open: bool
    generated_at: datetime
    digest: list[DigestItem]
    digest_narrative: str
    items: list[WatchlistEntryOut]


class SymbolSearchResult(BaseModel):
    symbol: str
    name: str
    sector: str
