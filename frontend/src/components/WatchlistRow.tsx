import { useState } from "react";
import type { ConvictionTier, WatchlistEntry } from "../types";
import FreshnessBadge from "./FreshnessBadge";
import ScoreMeter from "./ScoreMeter";
import Sparkline from "./Sparkline";
import RowDetail from "./RowDetail";

const SECTOR_COLORS: Record<string, string> = {
  IT: "text-sky-300 bg-sky-400/10",
  Banking: "text-indigo-300 bg-indigo-400/10",
  NBFC: "text-violet-300 bg-violet-400/10",
  Auto: "text-orange-300 bg-orange-400/10",
  Pharma: "text-teal-300 bg-teal-400/10",
  FMCG: "text-lime-300 bg-lime-400/10",
  Energy: "text-yellow-300 bg-yellow-400/10",
  Metals: "text-zinc-300 bg-zinc-400/10",
  Cement: "text-stone-300 bg-stone-400/10",
  Telecom: "text-fuchsia-300 bg-fuchsia-400/10",
  Infrastructure: "text-amber-300 bg-amber-400/10",
  "Consumer Durables": "text-pink-300 bg-pink-400/10",
  Chemicals: "text-cyan-300 bg-cyan-400/10",
};

export default function WatchlistRow({
  entry, onRemove, onTierChange,
}: {
  entry: WatchlistEntry;
  onRemove: (symbol: string) => void;
  onTierChange: (symbol: string, tier: ConvictionTier) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const changeColor =
    entry.change_pct == null ? "text-slate-500" : entry.change_pct >= 0 ? "text-emerald-400" : "text-rose-400";

  const flagged = entry.is_new_since_last_visit || (entry.score_delta_since_last_seen ?? 0) >= 8;
  const hasDetail = entry.sparkline || entry.signals?.z_score != null;

  return (
    <div className={`group rounded-xl border transition-colors ${
      flagged ? "border-emerald-500/20 bg-emerald-500/[0.03]" : "border-white/5 hover:bg-white/[0.02]"
    }`}>
      <div className="flex items-center gap-4 px-4 py-3">
        <button
          onClick={() => hasDetail && setExpanded((e) => !e)}
          className={`w-4 shrink-0 text-slate-600 transition-transform ${hasDetail ? "hover:text-slate-400 cursor-pointer" : "opacity-0"} ${expanded ? "rotate-90" : ""}`}
          disabled={!hasDetail}
        >
          ▸
        </button>

        <div className="w-36 shrink-0">
          <div className="flex items-center gap-1.5">
            {flagged && <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 shrink-0" title="Changed since your last visit" />}
            <span className="font-semibold text-white text-sm truncate">{entry.symbol}</span>
          </div>
          <div className="flex items-center gap-1.5 mt-0.5">
            {entry.sector && (
              <span className={`text-[10px] px-1.5 py-0.5 rounded ${SECTOR_COLORS[entry.sector] || "text-slate-400 bg-slate-500/10"}`}>
                {entry.sector}
              </span>
            )}
          </div>
        </div>

        <div className="w-24 shrink-0">
          {entry.price != null ? (
            <>
              <div className="text-sm text-white tabular-nums">₹{entry.price.toFixed(2)}</div>
              <div className={`text-xs tabular-nums ${changeColor}`}>
                {entry.change_pct != null ? `${entry.change_pct >= 0 ? "+" : ""}${entry.change_pct.toFixed(2)}%` : "—"}
              </div>
            </>
          ) : (
            <div className="text-xs text-slate-500">No data yet</div>
          )}
        </div>

        <div className="w-20 shrink-0 hidden sm:block">
          {entry.sparkline ? <Sparkline values={entry.sparkline} width={72} height={26} /> : <span className="text-slate-700 text-xs">—</span>}
        </div>

        <div className="w-28 shrink-0">
          <ScoreMeter score={entry.attention_score} />
        </div>

        <div className="flex-1 min-w-0" title={entry.signals?.explanation}>
          <p className="text-xs text-slate-400 truncate whitespace-nowrap">{entry.signals?.explanation}</p>
          {entry.signals?.sector_relative && (
            <span className={`text-[10px] mt-0.5 inline-block whitespace-nowrap truncate max-w-full ${entry.signals.sector_relative === "sector-wide" ? "text-slate-500" : "text-amber-400"}`}>
              {entry.signals.sector_relative === "sector-wide" ? "Sector-wide move" : "Moving alone vs. sector"}
            </span>
          )}
          {entry.insufficient_history && (
            <span className="text-[10px] mt-0.5 inline-block whitespace-nowrap text-slate-600">Building history…</span>
          )}
        </div>

        <div className="shrink-0 flex rounded-lg border border-white/10 overflow-hidden text-[11px]">
          {(["core", "trading"] as ConvictionTier[]).map((tier) => (
            <button
              key={tier}
              onClick={() => onTierChange(entry.symbol, tier)}
              className={`px-2.5 py-1 transition-colors capitalize ${
                entry.conviction_tier === tier ? "bg-emerald-500 text-slate-950 font-medium" : "text-slate-400 hover:bg-white/5"
              }`}
            >
              {tier}
            </button>
          ))}
        </div>

        <div className="w-20 shrink-0 flex items-center justify-end gap-2">
          {entry.price != null && (
            <FreshnessBadge isStale={entry.is_stale} fetchedAt={entry.fetched_at} source={entry.source} />
          )}
        </div>

        <button
          onClick={() => onRemove(entry.symbol)}
          className="shrink-0 text-slate-600 hover:text-rose-400 opacity-0 group-hover:opacity-100 transition-opacity px-1"
          title="Remove from watchlist"
        >
          ✕
        </button>
      </div>

      {expanded && hasDetail && <RowDetail entry={entry} />}
    </div>
  );
}
