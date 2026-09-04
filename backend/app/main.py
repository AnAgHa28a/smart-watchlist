import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.routers import auth, watchlist
from app.services.poller import poller_loop
from app.services.market_hours import is_market_open
from app.services.circuit_breaker import data_source_breaker

logging.basicConfig(level=logging.INFO)

_stop_event = asyncio.Event()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    task = asyncio.create_task(poller_loop(_stop_event))
    yield
    _stop_event.set()
    await task


app = FastAPI(title="Smart Watchlist API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(watchlist.router)


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/system/status")
def system_status():
    """Transparency endpoint: shows which upstream data sources are
    currently healthy vs circuit-broken, and whether the market is open.
    Exists so the resilience design is visible, not just claimed."""
    return {
        "market_open": is_market_open(),
        "data_sources": data_source_breaker.status(),
    }
