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
    is_extended_move: bool = False


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

    sparkline: list[float] | None = None
    score_sparkline: list[float] | None = None
    high_52w: float | None = None
    low_52w: float | None = None
    relative_strength_pct: float | None = None  # change_pct - sector_avg_move_pct

    active_alert_count: int = 0
    triggered_alert_count: int = 0


class DigestItem(BaseModel):
    symbol: str
    headline: str
    attention_score: float
    reason: str


class SectorAllocationEntry(BaseModel):
    sector: str
    count: int
    pct: float


class CorrelatedPairOut(BaseModel):
    symbol_a: str
    symbol_b: str
    correlation: float
    same_sector: bool


class WatchlistInsights(BaseModel):
    sector_allocation: list[SectorAllocationEntry]
    concentration_warning: str | None = None
    correlated_pairs: list[CorrelatedPairOut] = []


class WatchlistResponse(BaseModel):
    market_open: bool
    generated_at: datetime
    digest: list[DigestItem]
    digest_narrative: str
    items: list[WatchlistEntryOut]
    insights: WatchlistInsights | None = None


class SymbolSearchResult(BaseModel):
    symbol: str
    name: str
    sector: str


class SectorPulse(BaseModel):
    sector: str
    avg_move_pct: float
    symbol_count: int
    flagged_count: int


class TopMover(BaseModel):
    symbol: str
    name: str | None = None
    sector: str | None = None
    change_pct: float
    attention_score: float


class MarketPulseResponse(BaseModel):
    generated_at: datetime
    market_open: bool
    universe_size: int
    flagged_count: int
    sectors: list[SectorPulse]
    top_movers: list[TopMover]


class TrackRecordBucket(BaseModel):
    label: str
    count: int
    continued_pct: float


class TrackRecordResponse(BaseModel):
    total_graded: int
    continued_pct: float
    reverted_pct: float
    flat_pct: float
    backtest_count: int
    live_count: int
    live_pending: int
    buckets: list[TrackRecordBucket]


# --- Alerts ---
class CreateAlertRuleRequest(BaseModel):
    rule_type: str  # "price_above" | "price_below" | "volume_multiple"
    threshold: float = Field(gt=0)


class AlertRuleOut(BaseModel):
    id: int
    symbol: str
    rule_type: str
    threshold: float
    created_at: datetime
    triggered_at: datetime | None
    active: bool

    class Config:
        from_attributes = True
