import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type { WatchlistResponse } from "../types";

const LIVE_POLL_MS = 10_000;
const AWAY_THRESHOLD_MS = 60_000; // only re-"visit" if away for at least this long

export function useWatchlist() {
  const [data, setData] = useState<WatchlistResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const hiddenSinceRef = useRef<number | null>(null);

  const visit = useCallback(async () => {
    try {
      const res = await api.getWatchlist();
      setData(res);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load watchlist");
    } finally {
      setLoading(false);
    }
  }, []);

  const refreshLive = useCallback(async () => {
    try {
      const res = await api.getWatchlistLive();
      // Keep the digest/narrative from the last real visit; only refresh
      // the live-ticking fields (prices, scores, staleness, market_open).
      setData((prev) => (prev ? { ...prev, items: res.items, market_open: res.market_open } : res));
      setError(null);
    } catch {
      // A transient failure on a background poll shouldn't surface as a
      // page-level error — the next tick will retry.
    }
  }, []);

  useEffect(() => {
    visit();
  }, [visit]);

  useEffect(() => {
    const interval = setInterval(() => {
      if (!document.hidden) refreshLive();
    }, LIVE_POLL_MS);
    return () => clearInterval(interval);
  }, [refreshLive]);

  useEffect(() => {
    const onVisibilityChange = () => {
      if (document.hidden) {
        hiddenSinceRef.current = Date.now();
      } else if (hiddenSinceRef.current && Date.now() - hiddenSinceRef.current >= AWAY_THRESHOLD_MS) {
        visit();
      }
      hiddenSinceRef.current = document.hidden ? Date.now() : null;
    };
    document.addEventListener("visibilitychange", onVisibilityChange);
    return () => document.removeEventListener("visibilitychange", onVisibilityChange);
  }, [visit]);

  return { data, loading, error, revisit: visit };
}
