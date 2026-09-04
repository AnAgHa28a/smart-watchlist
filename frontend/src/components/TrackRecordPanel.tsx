import type { TrackRecordResponse } from "../types";

const CONTINUED = "#3987e5";
const REVERTED = "#c98500";
const FLAT = "#52514e";

export default function TrackRecordPanel({ data }: { data: TrackRecordResponse }) {
  if (data.total_graded === 0) return null;

  const maxBucketPct = Math.max(...data.buckets.map((b) => b.continued_pct), 1);

  return (
    <div className="rounded-2xl border border-white/5 bg-[#0f1520] p-4 mb-6">
      <div className="flex items-baseline justify-between mb-1">
        <h3 className="text-xs font-medium text-slate-400">Track record — is this signal actually useful?</h3>
        <span className="text-[11px] text-slate-600">
          {data.backtest_count} backtested{data.live_count > 0 && ` + ${data.live_count} live`}
          {data.live_pending > 0 && ` (${data.live_pending} maturing)`}
        </span>
      </div>
      <p className="text-[11px] text-slate-500 mb-3">
        Of every flag the algorithm has raised, replayed against a year of real prices — what happened over the next 5 sessions.
      </p>

      <div className="h-2 rounded-full overflow-hidden flex mb-2" style={{ gap: "2px" }}>
        <div style={{ width: `${data.continued_pct}%`, background: CONTINUED }} title={`Continued: ${data.continued_pct}%`} />
        <div style={{ width: `${data.reverted_pct}%`, background: REVERTED }} title={`Reverted: ${data.reverted_pct}%`} />
        <div style={{ width: `${data.flat_pct}%`, background: FLAT }} title={`Flat: ${data.flat_pct}%`} />
      </div>
      <div className="flex gap-4 mb-4">
        <Legend color={CONTINUED} label="Continued" pct={data.continued_pct} />
        <Legend color={REVERTED} label="Reverted" pct={data.reverted_pct} />
        <Legend color={FLAT} label="Flat" pct={data.flat_pct} />
      </div>

      <div className="pt-3 border-t border-white/5">
        <p className="text-[11px] text-slate-500 mb-2">Continuation rate by score — does a higher score mean more signal?</p>
        <div className="space-y-1.5">
          {data.buckets.map((b) => (
            <div key={b.label} className="flex items-center gap-3">
              <span className="w-16 shrink-0 text-[11px] text-slate-400">{b.label}</span>
              <div className="flex-1 h-1.5 rounded-full bg-white/5 overflow-hidden">
                <div className="h-full rounded-full" style={{ width: `${(b.continued_pct / maxBucketPct) * 100}%`, background: CONTINUED }} />
              </div>
              <span className="w-24 shrink-0 text-right text-[11px] text-slate-500 tabular-nums">
                {b.continued_pct}% <span className="text-slate-700">({b.count})</span>
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function Legend({ color, label, pct }: { color: string; label: string; pct: number }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="h-2 w-2 rounded-full shrink-0" style={{ background: color }} />
      <span className="text-[11px] text-slate-400">{label}</span>
      <span className="text-[11px] text-slate-600 tabular-nums">{pct}%</span>
    </div>
  );
}
