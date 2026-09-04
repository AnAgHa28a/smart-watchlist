from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, AlertRule, AlertRuleType, WatchlistItem
from app.schemas import CreateAlertRuleRequest, AlertRuleOut
from app.auth import get_current_user

router = APIRouter(prefix="/watchlist/items", tags=["alerts"])

VALID_TYPES = {t.value for t in AlertRuleType}


@router.get("/{symbol}/alerts", response_model=list[AlertRuleOut])
def list_alerts(symbol: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    symbol = symbol.strip().upper()
    return db.query(AlertRule).filter(AlertRule.user_id == user.id, AlertRule.symbol == symbol).all()


@router.post("/{symbol}/alerts", response_model=AlertRuleOut, status_code=201)
def create_alert(
    symbol: str, payload: CreateAlertRuleRequest,
    user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    symbol = symbol.strip().upper()
    if payload.rule_type not in VALID_TYPES:
        raise HTTPException(status_code=400, detail=f"rule_type must be one of {sorted(VALID_TYPES)}")

    owns_symbol = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == user.id, WatchlistItem.symbol == symbol
    ).first()
    if not owns_symbol:
        raise HTTPException(status_code=404, detail="Add this symbol to your watchlist before setting an alert on it")

    rule = AlertRule(
        user_id=user.id, symbol=symbol,
        rule_type=AlertRuleType(payload.rule_type), threshold=payload.threshold,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/{symbol}/alerts/{alert_id}")
def delete_alert(symbol: str, alert_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rule = db.query(AlertRule).filter(AlertRule.id == alert_id, AlertRule.user_id == user.id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Alert not found")
    db.delete(rule)
    db.commit()
    return {"ok": True}
