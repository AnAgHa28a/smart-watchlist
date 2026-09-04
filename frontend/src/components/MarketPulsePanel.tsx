import type { MarketPulseResponse } from "../types";

const GOOD = "#0ca30c";
const CRITICAL = "#e66767";

function DivergingBar({ pct, maxAbs }: { pct: number; maxAbs: number }) {
  const magnitude = maxAbs > 0 ? Math.min(Math.abs(pct) / maxAbs, 1) : 0;
  const color = pct >= 0 ? GOOD : CRITICAL;
  return (
    <div className="relative flex-1 h-2">
      <div className="absolute left-1/2 top-0 bottom-0 w-px bg-white/10" />
      <div
        className="absolute top-0 h-2 rounded-sm"
        style={{
          background: color,
          width: `${magnitude * 50}%`,
          left: pct >= 0 ? "50%" : `${50 - magnitude * 50}%`,
        }}
      />
    </div>
  );
}

export default function MarketPulsePanel({ pulse }: { pulse: MarketPulseResponse }) {
  const maxAbs = Math.max(...pulse.sectors.map((s) => Math.abs(s.avg_move_pct)), 0.5);

  return (
    <div className="rounded-2xl border border-white/5 bg-[#0f1520] p-4 mb-6">
      <div className="flex items-baseline justify-between mb-4">
        <h3 className="text-xs font-medium text-slate-400">Market pulse — beyond your watchlist</h3>
        <span className="text-[11px] text-slate-500">
          <span className="text-white font-medium tabular-nums">{pulse.flagged_count}</span> of{" "}
          <span className="tabular-nums">{pulse.universe_size}</span> tracked stocks flagged today
        </span>
      </div>

      <div className="space-y-2 mb-4">
        {pulse.sectors.map((s) => (
          <div key={s.sector} className="flex items-center gap-3">
            <span className="w-28 shrink-0 text-[11px] text-slate-400 truncate">{s.sector}</span>
            <DivergingBar pct={s.avg_move_pct} maxAbs={maxAbs} />
            <span className={`w-14 shrink-0 text-right text-[11px] tabular-nums ${s.avg_move_pct >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
              {s.avg_move_pct >= 0 ? "+" : ""}{s.avg_move_pct.toFixed(2)}%
            </span>
          </div>
        ))}
      </div>

      {pulse.top_movers.length > 0 && (
        <div className="pt-3 border-t border-white/5">
          <p className="text-[11px] text-slate-500 mb-2">Most unusual across the tracked universe</p>
          <div className="flex gap-2 overflow-x-auto pb-0.5">
            {pulse.top_movers.map((m) => (
              <div key={m.symbol} className="shrink-0 rounded-lg bg-white/[0.03] border border-white/5 px-2.5 py-1.5">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium text-white">{m.symbol}</span>
                  <span className={`text-[11px] tabular-nums ${m.change_pct >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                    {m.change_pct >= 0 ? "+" : ""}{m.change_pct.toFixed(1)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
