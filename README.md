# Signal — a smarter stock watchlist

**Live demo:** https://smart-watchlist-six.vercel.app
**API:** https://smart-watchlist-6nja.onrender.com (free tier, sleeps when idle — first request after a while can take ~50s to wake up)

Most watchlists just show you prices. Signal ranks each stock by how unusual its behavior actually is, remembers what you last saw, and tells you in plain language what's actually worth a look today.

Built for Groww's hackathon brief: a watchlist that shows what's meaningfully changed since you last checked.

### Jump to
[The core idea](#the-core-idea) · [Non-obvious choices](#three-deliberate-choices) · [Beyond the watchlist](#beyond-the-watchlist-itself) · [Architecture](#architecture) · [The brief's questions, answered](#answering-the-briefs-questions-directly) · [NSE data problem](#solving-the-nse-data-problem) · [Setup](#setup) · [100-word pitch](#the-100-word-pitch)

### A few things worth knowing

- **The core feature is a diff.** Every visit, the backend compares what you're seeing now against a snapshot of what you saw last time, stored server-side, and shows you only what's actually new.
- **The score is backtested.** [`backtest.py`](backend/app/services/backtest.py) replays the same scoring function across a year of real prices and grades every flag it would have raised. Higher-confidence flags really do hold up better — see **Track record** in the app.
- **NSE doesn't have a usable free API, so I dealt with that head-on.** `nseindia.com` blocks even a proper browser request. Prices come through a source cascade with a circuit breaker, and stale data always gets labeled.
- **It's live.** Real Postgres, real login, tested end to end.

---

## The core idea

A 0.5% move means nothing for a stable large-cap but could matter a lot for a quieter stock. So instead of a flat % change, every stock gets an **Attention Score (0–100)** based on how it's behaving relative to its own history:

| Signal | What it measures |
|---|---|
| Z-score of today's move | Today's return vs. the stock's own volatility — not a fixed "±2%" cutoff |
| Volume ratio | Today's volume vs. its 20-day average |
| 52-week level crossing | Whether the price is near a structural high or low |
| Gap % | The jump between yesterday's close and today's open |

That's the algorithm. The actual product is what happens next: every time you open your watchlist, the backend compares it to a snapshot of what you saw last time and writes a short summary of what's genuinely new, above the ranked list.

## Three deliberate choices

**1. Conviction tiers.** Tag a stock `Core` (long-term — only flag big structural moves) or `Trading` (flag smaller moves too). The same 1% move means something different depending on the tag, because "meaningful" isn't the same for every stock or every person.

**2. Sector-relative clustering.** Every move gets compared to how its sector did that same day. Four IT stocks all down 2% together is market noise. One stock down 2% alone is worth a look. Uses a static NIFTY sector map ([`nifty_universe.json`](backend/app/data/nifty_universe.json)).

**3. A grounded digest.** The "since you last checked" summary is templated by default — no external dependency to break during a demo — with an optional LLM rewrite when `ANTHROPIC_API_KEY` is set. Either way, it can only describe facts already computed, never invent numbers.

## Beyond the watchlist itself

Eight smaller additions. The first two are the ones I'd point you to first:

| Feature | Why it's there |
|---|---|
| **Self-graded track record** | Runs the scoring function against a year of real prices to see how it would've actually done. Higher-confidence flags do hold up better than lower-confidence ones — the score isn't just noise. |
| **Cross-stock correlation** | Sector tags catch the obvious overlap ("80% IT"), but miss two stocks in different sectors that still move together. This checks the real correlation in their price history. |
| **Market Pulse** | Shows how every tracked sector is doing today, not just your own list — tells you if a move is market-wide or specific to your stock. |
| **Sector concentration warning** | Flags it when one sector makes up over half your watchlist. |
| **Custom alerts** | Set a price or volume trigger per stock, on top of the Core/Trading tiers. |
| **Real sparklines** | Pulled from the year of price history already fetched for volatility, not a decorative chart. |
| **Per-stock drill-down** | Click a row to see the 52-week range, volatility, volume, and how it's doing versus its sector. |
| **Extended-move flag** | Flags large statistical outliers (>2.5σ) with a note that these often partly reverse — a framing hint, not a prediction. |

## Architecture

```
                    ┌─────────────────────────┐
                    │   Single background      │
                    │   poller (app/services/  │
                    │   poller.py)              │
                    │                           │
                    │  Polls the FIXED ~80-     │
                    │  symbol NSE universe —    │
                    │  not per-user, per-list.  │
                    │  Adding user #10,000      │
                    │  adds zero upstream calls.│
                    └────────────┬──────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
       NSE live quote      Yahoo Finance      Postgres cache
       (best-effort,       chart API          (price_snapshots,
       usually circuit-    (verified          symbol_stats) —
       broken open —       reliable from      survives backend
       NSE blocks cloud    a cloud host)      restarts
       IPs — see below)
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │   FastAPI backend         │
                    │   • attention_score.py    │
                    │   • sector_analysis.py    │
                    │   • watchlist_service.py  │
                    │     (the diff engine)     │
                    │   • digest.py (NL brief)  │
                    └────────────┬──────────────┘
                                 │  REST (cookie session)
                                 ▼
                    ┌─────────────────────────┐
                    │   React + Vite frontend   │
                    │   Digest panel + ranked   │
                    │   watchlist, live-        │
                    │   polling for prices,     │
                    │   separate "visit" call   │
                    │   for the diff/digest      │
                    └───────────────────────────┘
```

**Backend:** Python, FastAPI, Postgres (SQLAlchemy). **Frontend:** React, Vite, TypeScript, Tailwind. **Auth:** email/password, JWT in an httpOnly cookie — a real account, since syncing across devices is a server problem, not a browser one.

## Answering the brief's questions directly

The brief leaves six things open. Here's the direct answer to each:

| The brief asks... | Our answer |
|---|---|
| What counts as a **meaningful change**? | A volatility-adjusted score ([`attention_score.py`](backend/app/services/attention_score.py)), thresholded differently per conviction tier. |
| What **information to surface**? | Not just a price — a plain sentence explaining why it's flagged (e.g. "Up 3.2%, 2.8x its usual move, near its 52-week high"), plus the sector context. |
| How does **state persist across sessions/devices**? | Server-side Postgres, keyed by user id. Log in anywhere and see the same watchlist and the same "last seen" state ([`UserSymbolCheckpoint`](backend/app/models.py)). |
| How to handle **stale/delayed/conflicting data**? | A source cascade with a circuit breaker (details [below](#solving-the-nse-data-problem)). Every price is labeled live or stale, never silently wrong. |
| How does the system **scale**? | One poller tracks the fixed symbol universe no matter how many users sign up — cost scales with the universe, not with users × watchlists. Every client reads a shared cache instead of triggering its own fetch. |
| Where to keep it **simple vs. add complexity**? | Polling instead of WebSockets, a curated symbol list instead of open search, no options chain or portfolio P&L or ML model — each a deliberate cut to fit the time box. |

## Solving the NSE data problem

There's no free, reliable, real-time NSE data source — confirmed directly while building this: `nseindia.com` returns `403` even with a normal browser User-Agent. Rather than pretend otherwise, this is treated as a real constraint:

1. **Cascading sources.** NSE's own quote endpoint is tried first, then Yahoo Finance's chart API (called directly over HTTPS, not through the `yfinance` package — a plain `httpx` request with a browser header works fine and is more reliable), then the last known-good value from Postgres, marked stale.
2. **A circuit breaker per source** ([`circuit_breaker.py`](backend/app/services/circuit_breaker.py)) so a failing source gets skipped for a cooldown instead of hammered every cycle — visible live at `GET /system/status`.
3. **A statistical baseline from the same Yahoo endpoint**, not NSE's Bhavcopy archives (also unreachable in practice). One `range=1y` call per symbol backfills a year of daily prices, so volatility and 52-week range are grounded from day one instead of showing "not enough history."

## Why polling over WebSockets

A deliberate simplicity call. A single naive polling endpoint would mark every symbol "seen" on every tick, collapsing the digest to empty within seconds — so there are two endpoints instead of one:

- `GET /watchlist` — a **visit**. Diffs against and advances the checkpoint, computes the digest. Called on page load and when the tab regains focus.
- `GET /watchlist/live` — a **passive refresh**. Current prices only, never touches the checkpoint. Polled every ~10s to keep numbers ticking without disturbing what "since you last checked" means.

WebSockets would add real polish, but this gets most of the benefit with far less deployment risk, and the scaling design doesn't depend on push transport either way.

---

## Setup

### Backend

```bash
cd backend
python3.13 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in DATABASE_URL at minimum
uvicorn app.main:app --reload
```

Needs Python 3.11–3.13 (not 3.14 yet — some dependencies don't have prebuilt wheels) and a Postgres database (local, or a free Neon/Supabase instance).

`ANTHROPIC_API_KEY` is optional — leave it out and the digest falls back to the template automatically.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env   # VITE_API_URL should point at the backend
npm run dev
```

### Deploying

Deployed here on Render (backend) + Vercel (frontend) + Neon (Postgres), all free tier:

- **Neon** — create a project, copy the connection string into `DATABASE_URL`.
- **Render** — New Web Service, Docker runtime. Set **Dockerfile Path** to `backend/Dockerfile` and **Docker Build Context Directory** to `backend` explicitly (Root Directory alone wasn't reliable — it built against the repo root and couldn't find the Dockerfile). Env vars: `DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS`, `COOKIE_SECURE=true`, `COOKIE_SAMESITE=none`. Render's free tier now asks for a card on file even though it's $0.
- **Vercel** — import with Root Directory `frontend`; Vite is auto-detected. Set `VITE_API_URL` to the Render URL. Needs the included `vercel.json` rewrite, or direct navigation to routes like `/login` 404s.
- Both auto-redeploy on every push to `main` — Render rebuilds even for frontend-only commits, which is harmless, just an extra build.

## What I'd add with more time

- An NSE holiday calendar — market hours are currently weekday + time only, which is fine 99% of the time but can be a little off around holidays.
- WebSocket push for true real-time ticking.
- Push/email delivery for alerts. The triggers exist and surface in-app, but there's no way to notify you while you're away from the tab.

---

## The 100-word pitch

Signal is a watchlist built around one question: what actually deserves my attention today? Each stock gets an Attention Score based on its own volatility, volume, and how its sector is doing — not a flat percentage cutoff. A server-side checkpoint per user powers a real "since you last checked" summary across devices. The part I'm proudest of: a backtest that replays the same algorithm across a year of real prices, so you can see its hit rate — higher-confidence flags do better than lower ones. It's also built around a real constraint: free real-time NSE data doesn't exist, so the system pulls from multiple sources and is upfront when data is stale.
