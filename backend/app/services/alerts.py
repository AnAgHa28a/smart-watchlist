"""Evaluates user-defined alert rules against the shared price cache.

Runs once per poll cycle, not per-request — same O(universe), not O(users),
scaling principle as the rest of the poller: checking 10,000 users' rules
costs the same one pass over price_snapshots regardless of how many rules
exist, since it's one query joined against the cache, not one fetch per rule.
"""
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import AlertRule, AlertRuleType, PriceSnapshot, SymbolStats


def evaluate_alert_rules(db: Session) -> None:
    active_rules = db.query(AlertRule).filter(
        AlertRule.active.is_(True), AlertRule.triggered_at.is_(None)
    ).all()
    if not active_rules:
        return

    symbols = {r.symbol for r in active_rules}
    snapshots = {
        row.symbol: row for row in db.query(PriceSnapshot).filter(PriceSnapshot.symbol.in_(symbols)).all()
    }
    stats = {
        row.symbol: row for row in db.query(SymbolStats).filter(SymbolStats.symbol.in_(symbols)).all()
    }

    now = datetime.utcnow()
    for rule in active_rules:
        snap = snapshots.get(rule.symbol)
        if snap is None or snap.is_stale or snap.price is None:
            continue

        triggered = False
        if rule.rule_type == AlertRuleType.price_above:
            triggered = snap.price >= rule.threshold
        elif rule.rule_type == AlertRuleType.price_below:
            triggered = snap.price <= rule.threshold
        elif rule.rule_type == AlertRuleType.volume_multiple:
            avg_volume = stats.get(rule.symbol) and stats[rule.symbol].avg_volume_20d
            if snap.volume and avg_volume:
                triggered = (snap.volume / avg_volume) >= rule.threshold

        if triggered:
            rule.triggered_at = now

    db.commit()
