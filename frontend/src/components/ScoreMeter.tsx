export default function ScoreMeter({ score }: { score: number | null }) {
  if (score === null) return <span className="text-slate-600 text-xs">—</span>;

  const color =
    score >= 55 ? "bg-rose-400" : score >= 30 ? "bg-amber-400" : "bg-slate-600";
  const textColor =
    score >= 55 ? "text-rose-300" : score >= 30 ? "text-amber-300" : "text-slate-500";

  return (
    <div className="flex items-center gap-2 w-24">
      <div className="h-1.5 flex-1 rounded-full bg-white/5 overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all`} style={{ width: `${Math.min(score, 100)}%` }} />
      </div>
      <span className={`text-xs font-medium tabular-nums ${textColor}`}>{score.toFixed(0)}</span>
    </div>
  );
}
