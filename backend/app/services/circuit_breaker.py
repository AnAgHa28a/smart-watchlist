"""A tiny in-memory circuit breaker per data source.

Free NSE-adjacent data sources fail in bursts (rate limiting, bot detection,
transient outages). Retrying blindly on every poll cycle makes things worse —
it hammers a source that's already struggling and can get our IP banned
outright. Instead: after a few consecutive failures, stop calling that source
for a cooldown window and fall through to the next one in the cascade.
"""
import time
import threading


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, cooldown_seconds: int = 300):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self._failures: dict[str, int] = {}
        self._open_until: dict[str, float] = {}
        self._lock = threading.Lock()

    def is_open(self, source: str) -> bool:
        """True if this source should be skipped right now."""
        with self._lock:
            until = self._open_until.get(source, 0)
            if until and time.time() < until:
                return True
            if until and time.time() >= until:
                # cooldown elapsed, allow a probe attempt
                self._open_until.pop(source, None)
                self._failures[source] = 0
            return False

    def record_success(self, source: str) -> None:
        with self._lock:
            self._failures[source] = 0
            self._open_until.pop(source, None)

    def record_failure(self, source: str) -> None:
        with self._lock:
            count = self._failures.get(source, 0) + 1
            self._failures[source] = count
            if count >= self.failure_threshold:
                self._open_until[source] = time.time() + self.cooldown_seconds

    def status(self) -> dict:
        with self._lock:
            now = time.time()
            return {
                src: {
                    "failures": self._failures.get(src, 0),
                    "open": bool(until and now < until),
                    "reopens_in_s": max(0, int(until - now)) if until else 0,
                }
                for src, until in {**{s: 0 for s in self._failures}, **self._open_until}.items()
            }


data_source_breaker = CircuitBreaker(failure_threshold=3, cooldown_seconds=300)
