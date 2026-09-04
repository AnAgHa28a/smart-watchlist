export type ConvictionTier = "core" | "trading";

export interface User {
  id: number;
  email: string;
}

export interface SignalBreakdown {
  z_score: number | null;
  volume_ratio: number | null;
  near_52w_high: boolean;
  near_52w_low: boolean;
  gap_pct: number | null;
  sector_relative: "sector-wide" | "idiosyncratic" | null;
  sector_avg_move_pct: number | null;
  explanation: string;
}

export interface WatchlistEntry {
  symbol: string;
  name: string | null;
  sector: string | null;
  conviction_tier: ConvictionTier;
  price: number | null;
  prev_close: number | null;
  change_pct: number | null;
  volume: number | null;
  is_stale: boolean;
  source: string | null;
  fetched_at: string | null;
  attention_score: number | null;
  signals: SignalBreakdown | null;
  is_new_since_last_visit: boolean;
  price_change_since_last_seen: number | null;
  price_change_pct_since_last_seen: number | null;
  score_delta_since_last_seen: number | null;
  last_seen_at: string | null;
  insufficient_history: boolean;
}

export interface DigestItem {
  symbol: string;
  headline: string;
  attention_score: number;
  reason: string;
}

export interface WatchlistResponse {
  market_open: boolean;
  generated_at: string;
  digest: DigestItem[];
  digest_narrative: string;
  items: WatchlistEntry[];
}

export interface SymbolSearchResult {
  symbol: string;
  name: string;
  sector: string;
}
