const TRACK = "rgba(255,255,255,0.06)";

function severityColor(fraction: number): string {
  if (fraction >= 0.75) return "#e66767"; // danger
  if (fraction >= 0.4) return "#c98500"; // warning
  return "#3987e5"; // accent
}

export function Meter({
  label, fraction, valueLabel,
}: { label: string; fraction: number; valueLabel: string }) {
  const clamped = Math.max(0, Math.min(fraction, 1));
  const color = severityColor(clamped);
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-[11px] text-slate-500">{label}</span>
        <span className="text-[11px] font-medium tabular-nums" style={{ color }}>{valueLabel}</span>
      </div>
      <div className="h-1.5 rounded-full overflow-hidden" style={{ background: TRACK }}>
        <div className="h-full rounded-full transition-all" style={{ width: `${clamped * 100}%`, background: color }} />
      </div>
    </div>
  );
}

export function RangePosition({
  low, high, price,
}: { low: number; high: number; price: number }) {
  const range = high - low || 1;
  const pct = Math.max(0, Math.min(((price - low) / range) * 100, 100));
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-[11px] text-slate-500">52-week range</span>
        <span className="text-[11px] text-slate-400 tabular-nums">₹{low.toFixed(0)} – ₹{high.toFixed(0)}</span>
      </div>
      <div className="h-1.5 rounded-full relative" style={{ background: "linear-gradient(90deg, #e6676733, #3987e533, #0ca30c33)" }}>
        <div
          className="absolute top-1/2 -translate-y-1/2 h-2.5 w-2.5 rounded-full bg-white shadow ring-2 ring-[#0a0e14]"
          style={{ left: `calc(${pct}% - 5px)` }}
        />
      </div>
    </div>
  );
}
