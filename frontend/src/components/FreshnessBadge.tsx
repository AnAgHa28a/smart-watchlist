function timeAgo(iso: string | null): string {
  if (!iso) return "";
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(iso + "Z").getTime()) / 1000));
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ago`;
}

export default function FreshnessBadge({
  isStale, fetchedAt, source,
}: { isStale: boolean; fetchedAt: string | null; source: string | null }) {
  if (isStale) {
    return (
      <span className="inline-flex items-center gap-1 text-[11px] text-amber-400/90 bg-amber-400/10 px-1.5 py-0.5 rounded"
            title={`Last known price${source ? ` from ${source}` : ""} — live sources unavailable this cycle`}>
        <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
        stale
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 text-[11px] text-slate-500" title={source ? `via ${source}` : ""}>
      <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
      {timeAgo(fetchedAt)}
    </span>
  );
}
