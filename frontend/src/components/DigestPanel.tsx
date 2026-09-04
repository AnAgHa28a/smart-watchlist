import type { DigestItem } from "../types";

export default function DigestPanel({
  digest, narrative, marketOpen,
}: { digest: DigestItem[]; narrative: string; marketOpen: boolean }) {
  return (
    <div className="rounded-2xl border border-white/5 bg-gradient-to-br from-[#131b2c] to-[#0f1520] p-5 mb-6">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <span className="text-emerald-400">●</span> Since you last checked
        </h2>
        <span className={`text-[11px] px-2 py-0.5 rounded-full ${marketOpen ? "bg-emerald-400/10 text-emerald-400" : "bg-slate-500/10 text-slate-400"}`}>
          {marketOpen ? "Market open" : "Market closed"}
        </span>
      </div>

      <p className="text-sm text-slate-300 leading-relaxed mb-4">{narrative}</p>

      {digest.length > 0 && (
        <div className="flex gap-3 overflow-x-auto pb-1 -mx-1 px-1">
          {digest.map((d) => (
            <div key={d.symbol} className="shrink-0 w-56 rounded-xl bg-white/[0.03] border border-white/5 p-3">
              <div className="flex items-center justify-between mb-1.5">
                <span className="font-semibold text-white text-sm">{d.symbol}</span>
                <span className="text-[11px] font-medium text-rose-300 bg-rose-400/10 px-1.5 py-0.5 rounded tabular-nums">
                  {d.attention_score.toFixed(0)}
                </span>
              </div>
              <p className="text-xs text-slate-400 leading-snug">{d.headline}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
