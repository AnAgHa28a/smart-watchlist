import { useEffect, useState } from "react";
import { api, ApiError } from "../api/client";
import type { ConvictionTier, SymbolSearchResult } from "../types";

export default function AddSymbolModal({
  onClose, onAdded,
}: { onClose: () => void; onAdded: () => void }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SymbolSearchResult[]>([]);
  const [selected, setSelected] = useState<SymbolSearchResult | null>(null);
  const [tier, setTier] = useState<ConvictionTier>("trading");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const handle = setTimeout(() => {
      api.searchSymbols(query).then(setResults).catch(() => setResults([]));
    }, 150);
    return () => clearTimeout(handle);
  }, [query]);

  const handleAdd = async () => {
    if (!selected) return;
    setSubmitting(true);
    setError(null);
    try {
      await api.addSymbol(selected.symbol, tier);
      onAdded();
      onClose();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to add symbol");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-start justify-center pt-24 z-50" onClick={onClose}>
      <div
        data-testid="add-symbol-modal"
        className="w-full max-w-md bg-[#111826] border border-white/10 rounded-2xl p-5 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="text-white font-semibold mb-3">Add a symbol</h3>
        <input
          autoFocus
          value={query}
          onChange={(e) => { setQuery(e.target.value); setSelected(null); }}
          placeholder="Search NSE symbol or company name…"
          className="w-full rounded-lg bg-[#0a0e14] border border-white/10 focus:border-emerald-500 focus:outline-none px-3 py-2.5 text-sm text-white placeholder:text-slate-600 mb-3"
        />

        {!selected && (
          <div className="max-h-56 overflow-y-auto space-y-1 mb-3">
            {results.map((r) => (
              <button
                key={r.symbol}
                onClick={() => { setSelected(r); setQuery(r.symbol); }}
                className="w-full text-left px-3 py-2 rounded-lg hover:bg-white/5 flex items-center justify-between"
              >
                <div>
                  <div className="text-sm text-white">{r.symbol}</div>
                  <div className="text-xs text-slate-500">{r.name}</div>
                </div>
                <span className="text-[10px] text-slate-500">{r.sector}</span>
              </button>
            ))}
            {query && results.length === 0 && (
              <p className="text-xs text-slate-500 px-3 py-2">No matches in the tracked NSE universe.</p>
            )}
          </div>
        )}

        {selected && (
          <div className="mb-4">
            <p className="text-xs text-slate-400 mb-2">
              Conviction tier for <span className="text-white font-medium">{selected.symbol}</span>
            </p>
            <div className="flex gap-2">
              {(["trading", "core"] as ConvictionTier[]).map((t) => (
                <button
                  key={t}
                  onClick={() => setTier(t)}
                  className={`flex-1 rounded-lg border px-3 py-2 text-sm capitalize transition-colors ${
                    tier === t ? "border-emerald-500 bg-emerald-500/10 text-emerald-300" : "border-white/10 text-slate-400 hover:bg-white/5"
                  }`}
                >
                  {t}
                  <div className="text-[10px] font-normal opacity-70 mt-0.5">
                    {t === "core" ? "Only flag structural moves" : "Flag smaller intraday moves"}
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {error && <p className="text-sm text-rose-400 mb-3">{error}</p>}

        <div className="flex gap-2 justify-end">
          <button onClick={onClose} className="px-3 py-2 text-sm text-slate-400 hover:text-white">
            Cancel
          </button>
          <button
            onClick={handleAdd}
            disabled={!selected || submitting}
            className="px-4 py-2 text-sm rounded-lg bg-emerald-500 hover:bg-emerald-400 disabled:opacity-40 text-slate-950 font-medium"
          >
            {submitting ? "Adding…" : "Add to watchlist"}
          </button>
        </div>
      </div>
    </div>
  );
}
