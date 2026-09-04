import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Date, Boolean, ForeignKey,
    UniqueConstraint, Enum, JSON,
)
from sqlalchemy.orm import relationship

from app.database import Base


class ConvictionTier(str, enum.Enum):
    core = "core"
    trading = "trading"


class DataSource(str, enum.Enum):
    yahoo = "yahoo"
    nse_live = "nse_live"
    cache = "cache"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    watchlist_items = relationship("WatchlistItem", back_populates="user", cascade="all, delete-orphan")


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"
    __table_args__ = (UniqueConstraint("user_id", "symbol", name="uq_user_symbol"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String, nullable=False, index=True)
    conviction_tier = Column(Enum(ConvictionTier), default=ConvictionTier.trading, nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="watchlist_items")


class PriceSnapshot(Base):
    """Market-wide LATEST price cache, one row per symbol (upserted, not
    appended) — shared across all users watching that symbol. A single
    poller writes here regardless of how many users or devices are watching;
    every watchlist read is just a cheap lookup against this table. Being a
    real DB table (not an in-memory dict) also means the cache survives a
    backend restart instead of needing a cold refetch of every symbol."""
    __tablename__ = "price_snapshots"

    symbol = Column(String, primary_key=True)
    price = Column(Float, nullable=False)
    volume = Column(Float, nullable=True)
    prev_close = Column(Float, nullable=True)
    open_price = Column(Float, nullable=True)
    source = Column(Enum(DataSource), nullable=False)
    is_stale = Column(Boolean, default=False)
    fetched_at = Column(DateTime, default=datetime.utcnow)


class SymbolStats(Base):
    """Rolling statistical baseline per symbol, seeded from a year of daily
    OHLCV (fetched from Yahoo's chart endpoint — see data_fetch.py for why
    NSE's own archives aren't a viable source) and refreshed daily. Powers
    the z-score / volume-ratio / 52w-high-low components of the attention
    score."""
    __tablename__ = "symbol_stats"

    symbol = Column(String, primary_key=True)
    daily_return_stdev = Column(Float, nullable=True)
    avg_volume_20d = Column(Float, nullable=True)
    high_52w = Column(Float, nullable=True)
    low_52w = Column(Float, nullable=True)
    history_days = Column(Integer, default=0)
    sector = Column(String, nullable=True)
    name = Column(String, nullable=True)
    # Trimmed trailing windows (~60 sessions), kept for the price and score
    # sparklines — both come free from data already fetched/computed during
    # backfill (see services/backtest.py), no extra requests.
    recent_closes = Column(JSON, nullable=True)
    recent_scores = Column(JSON, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow)


class FlagEvent(Base):
    """One row per (symbol, day) the algorithm judged 'meaningful' — the
    system's own track record. 'backtest' rows are produced once by
    replaying the algorithm day-by-day across a year of real historical
    prices (services/backtest.py — careful to use only data available as of
    that simulated day, no lookahead); 'live' rows are logged going forward
    by the poller. Both are graded the same way: did the move continue
    ~5 trading sessions later, or revert? This is what lets the product
    show an honest, immediately-populated hit rate instead of an empty
    promise on day one."""
    __tablename__ = "flag_events"
    __table_args__ = (UniqueConstraint("symbol", "event_date", "source", name="uq_flag_event"),)

    id = Column(Integer, primary_key=True)
    symbol = Column(String, nullable=False, index=True)
    event_date = Column(Date, nullable=False)
    score = Column(Float, nullable=False)
    price_at_flag = Column(Float, nullable=False)
    move_direction = Column(Integer, nullable=False)  # 1 = up, -1 = down, on the flagged day
    source = Column(String, nullable=False)  # "backtest" | "live"
    graded = Column(Boolean, default=False)
    outcome = Column(String, nullable=True)  # "continued" | "reverted" | "flat"
    forward_return_pct = Column(Float, nullable=True)
    graded_at = Column(DateTime, nullable=True)


class AlertRuleType(str, enum.Enum):
    price_above = "price_above"
    price_below = "price_below"
    volume_multiple = "volume_multiple"


class AlertRule(Base):
    """A user-defined trigger layered on top of the algorithmic score —
    'alert me specifically if X crosses this price' or 'if volume spikes
    this hard' — for the cases where a user wants control more direct than
    the Core/Trading tiers give them."""
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String, nullable=False)
    rule_type = Column(Enum(AlertRuleType), nullable=False)
    threshold = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    triggered_at = Column(DateTime, nullable=True)
    active = Column(Boolean, default=True)


class UserSymbolCheckpoint(Base):
    """The 'since you last checked' mechanism. One row per (user, symbol),
    updated whenever the user actually views that symbol. Diffing current
    state against this row is what produces the digest."""
    __tablename__ = "user_symbol_checkpoints"
    __table_args__ = (UniqueConstraint("user_id", "symbol", name="uq_checkpoint_user_symbol"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String, nullable=False)
    last_seen_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_seen_price = Column(Float, nullable=True)
    last_seen_attention_score = Column(Float, nullable=True)
