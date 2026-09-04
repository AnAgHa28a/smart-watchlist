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
  is_extended_move: boolean;
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

  sparkline: number[] | null;
  score_sparkline: number[] | null;
  high_52w: number | null;
  low_52w: number | null;
  relative_strength_pct: number | null;

  active_alert_count: number;
  triggered_alert_count: number;
}

export interface SectorAllocationEntry {
  sector: string;
  count: number;
  pct: number;
}

export interface CorrelatedPair {
  symbol_a: string;
  symbol_b: string;
  correlation: number;
  same_sector: boolean;
}

export interface WatchlistInsights {
  sector_allocation: SectorAllocationEntry[];
  concentration_warning: string | null;
  correlated_pairs: CorrelatedPair[];
}

export interface SectorPulse {
  sector: string;
  avg_move_pct: number;
  symbol_count: number;
  flagged_count: number;
}

export interface TopMover {
  symbol: string;
  name: string | null;
  sector: string | null;
  change_pct: number;
  attention_score: number;
}

export interface MarketPulseResponse {
  generated_at: string;
  market_open: boolean;
  universe_size: number;
  flagged_count: number;
  sectors: SectorPulse[];
  top_movers: TopMover[];
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
  insights: WatchlistInsights | null;
}

export interface SymbolSearchResult {
  symbol: string;
  name: string;
  sector: string;
}

export interface TrackRecordBucket {
  label: string;
  count: number;
  continued_pct: number;
}

export interface TrackRecordResponse {
  total_graded: number;
  continued_pct: number;
  reverted_pct: number;
  flat_pct: number;
  backtest_count: number;
  live_count: number;
  live_pending: number;
  buckets: TrackRecordBucket[];
}

export type AlertRuleType = "price_above" | "price_below" | "volume_multiple";

export interface AlertRule {
  id: number;
  symbol: string;
  rule_type: AlertRuleType;
  threshold: number;
  created_at: string;
  triggered_at: string | null;
  active: boolean;
}
