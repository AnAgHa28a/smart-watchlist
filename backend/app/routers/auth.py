from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import SignupRequest, LoginRequest, UserOut
from app.auth import hash_password, verify_password, create_access_token, get_current_user, COOKIE_NAME
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

COOKIE_MAX_AGE = settings.jwt_expire_minutes * 60


def _set_session_cookie(response: Response, user_id: int) -> None:
    token = create_access_token(user_id)
    response.set_cookie(
        key=COOKIE_NAME, value=token, max_age=COOKIE_MAX_AGE,
        httponly=True, samesite=settings.cookie_samesite, secure=settings.cookie_secure, path="/",
    )


@router.post("/signup", response_model=UserOut)
def signup(payload: SignupRequest, response: Response, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    _set_session_cookie(response, user.id)
    return user


@router.post("/login", response_model=UserOut)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    _set_session_cookie(response, user.id)
    return user


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"ok": True}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
