import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { MarketPulseResponse } from "../types";

const REFRESH_MS = 30_000;

export function useMarketPulse() {
  const [pulse, setPulse] = useState<MarketPulseResponse | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = () => {
      api.getMarketPulse().then((res) => { if (!cancelled) setPulse(res); }).catch(() => {});
    };
    load();
    const interval = setInterval(() => { if (!document.hidden) load(); }, REFRESH_MS);
    return () => { cancelled = true; clearInterval(interval); };
  }, []);

  return pulse;
}
