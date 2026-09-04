import type { WatchlistEntry } from "../types";
import Sparkline from "./Sparkline";
import { Meter, RangePosition } from "./SignalMeter";
import AlertsSection from "./AlertsSection";

export default function RowDetail({ entry }: { entry: WatchlistEntry }) {
  const s = entry.signals;

  return (
    <div className="px-4 pb-4 pt-1 border-t border-white/5 bg-white/[0.015]">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-4 pt-3">
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[11px] text-slate-500">60-session price trend</span>
            {entry.relative_strength_pct != null && (
              <span className={`text-[11px] tabular-nums ${entry.relative_strength_pct >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                {entry.relative_strength_pct >= 0 ? "+" : ""}{entry.relative_strength_pct.toFixed(2)}pp vs sector today
              </span>
            )}
          </div>
          {entry.sparkline ? (
            <Sparkline values={entry.sparkline} width={280} height={56} />
          ) : (
            <p className="text-xs text-slate-600">Building history…</p>
          )}
        </div>

        <div className="space-y-3">
          {entry.high_52w != null && entry.low_52w != null && entry.price != null && (
            <RangePosition low={entry.low_52w} high={entry.high_52w} price={entry.price} />
          )}
          {s?.z_score != null && (
            <div>
              <Meter label="Move vs. own volatility" fraction={Math.min(Math.abs(s.z_score) / 3, 1)} valueLabel={`${s.z_score.toFixed(2)}σ`} />
              {s.is_extended_move && (
                <p className="text-[10px] text-amber-400/80 mt-1" title="A statistical observation, not a prediction: moves this far from a stock's typical range regress toward it more often than they extend further.">
                  Extended move — historically these often partially revert
                </p>
              )}
            </div>
          )}
          {s?.volume_ratio != null && (
            <Meter label="Volume vs. 20-day avg" fraction={Math.min(Math.max(s.volume_ratio - 1, 0) / 3, 1)} valueLabel={`${s.volume_ratio.toFixed(1)}x`} />
          )}
          {s?.gap_pct != null && Math.abs(s.gap_pct) > 0.05 && (
            <Meter label="Gap at open" fraction={Math.min(Math.abs(s.gap_pct) / 5, 1)} valueLabel={`${s.gap_pct >= 0 ? "+" : ""}${s.gap_pct.toFixed(2)}%`} />
          )}
        </div>

        <div>
          <p className="text-[11px] text-slate-500 mb-1.5">Attention score trend — escalating or cooling off</p>
          {entry.score_sparkline && entry.score_sparkline.length > 1 ? (
            <Sparkline values={entry.score_sparkline} width={280} height={40} />
          ) : (
            <p className="text-xs text-slate-600">Building history…</p>
          )}
        </div>

        <div>
          <AlertsSection symbol={entry.symbol} />
        </div>
      </div>
    </div>
  );
}
