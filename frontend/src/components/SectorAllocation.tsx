import type { WatchlistInsights } from "../types";

// Validated dark-mode categorical palette, fixed order (see dataviz skill) —
// same sector always gets the same slot across the app, never re-cycled.
const CATEGORICAL = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767"];
const FOLD_LIMIT = 8;
const OTHER_COLOR = "#52514e";

export default function SectorAllocation({ insights }: { insights: WatchlistInsights }) {
  const entries = insights.sector_allocation;
  if (entries.length === 0) return null;

  const shown = entries.slice(0, FOLD_LIMIT);
  const rest = entries.slice(FOLD_LIMIT);
  const otherPct = rest.reduce((sum, e) => sum + e.pct, 0);
  const segments = [
    ...shown.map((e, i) => ({ label: e.sector, pct: e.pct, color: CATEGORICAL[i] })),
    ...(rest.length > 0 ? [{ label: "Other", pct: otherPct, color: OTHER_COLOR }] : []),
  ];

  return (
    <div className="rounded-2xl border border-white/5 bg-[#0f1520] p-4 mb-6">
      <h3 className="text-xs font-medium text-slate-400 mb-3">Watchlist composition</h3>

      <div className="h-2 rounded-full overflow-hidden flex mb-3" style={{ gap: "2px" }}>
        {segments.map((s) => (
          <div key={s.label} style={{ width: `${s.pct}%`, background: s.color }} title={`${s.label}: ${s.pct.toFixed(0)}%`} />
        ))}
      </div>

      <div className="flex flex-wrap gap-x-4 gap-y-1.5">
        {segments.map((s) => (
          <div key={s.label} className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full shrink-0" style={{ background: s.color }} />
            <span className="text-[11px] text-slate-400">{s.label}</span>
            <span className="text-[11px] text-slate-600 tabular-nums">{s.pct.toFixed(0)}%</span>
          </div>
        ))}
      </div>

      {insights.concentration_warning && (
        <div className="mt-3 flex items-start gap-2 text-[11px] text-amber-400/90 bg-amber-400/[0.06] rounded-lg px-2.5 py-2">
          <span className="shrink-0">⚠</span>
          <span>{insights.concentration_warning}</span>
        </div>
      )}
    </div>
  );
}
