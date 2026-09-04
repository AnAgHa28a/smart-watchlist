import { useState } from "react";
import { useAuth } from "../hooks/useAuth";
import { useWatchlist } from "../hooks/useWatchlist";
import { useMarketPulse } from "../hooks/useMarketPulse";
import { useTrackRecord } from "../hooks/useTrackRecord";
import { api } from "../api/client";
import DigestPanel from "../components/DigestPanel";
import WatchlistRow from "../components/WatchlistRow";
import AddSymbolModal from "../components/AddSymbolModal";
import SectorAllocation from "../components/SectorAllocation";
import MarketPulsePanel from "../components/MarketPulsePanel";
import TrackRecordPanel from "../components/TrackRecordPanel";
import type { ConvictionTier } from "../types";

export default function WatchlistPage() {
  const { user, logout } = useAuth();
  const { data, loading, error, revisit } = useWatchlist();
  const pulse = useMarketPulse();
  const trackRecord = useTrackRecord();
  const [showAddModal, setShowAddModal] = useState(false);

  const handleRemove = async (symbol: string) => {
    await api.removeSymbol(symbol);
    revisit();
  };

  const handleTierChange = async (symbol: string, tier: ConvictionTier) => {
    await api.updateTier(symbol, tier);
    revisit();
  };

  return (
    <div className="min-h-screen bg-[#0a0e14]">
      <header className="border-b border-white/5 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="h-7 w-7 rounded-lg bg-emerald-500 flex items-center justify-center text-slate-950 font-bold text-sm">S</div>
          <span className="text-white font-semibold">Signal</span>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-slate-500">{user?.email}</span>
          <button onClick={() => logout()} className="text-sm text-slate-400 hover:text-white">
            Log out
          </button>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8">
        {loading && (
          <div className="flex justify-center py-24">
            <div className="h-6 w-6 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {error && !loading && (
          <div className="rounded-xl border border-rose-500/20 bg-rose-500/5 p-4 text-sm text-rose-300 mb-6">
            Couldn't reach the server — {error}
          </div>
        )}

        {data && (
          <>
            <DigestPanel digest={data.digest} narrative={data.digest_narrative} marketOpen={data.market_open} />

            {pulse && <MarketPulsePanel pulse={pulse} />}

            {trackRecord && <TrackRecordPanel data={trackRecord} />}

            {data.insights && data.items.length > 0 && <SectorAllocation insights={data.insights} />}

            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-medium text-slate-400">
                Your watchlist {data.items.length > 0 && `(${data.items.length})`}
              </h2>
              <button
                onClick={() => setShowAddModal(true)}
                className="text-sm px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-white transition-colors"
              >
                + Add symbol
              </button>
            </div>

            {data.items.length === 0 ? (
              <div className="text-center py-20 border border-dashed border-white/10 rounded-2xl">
                <p className="text-slate-400 text-sm mb-3">Your watchlist is empty.</p>
                <button
                  onClick={() => setShowAddModal(true)}
                  className="text-sm px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-medium"
                >
                  Add your first symbol
                </button>
              </div>
            ) : (
              <div className="space-y-1.5">
                {data.items.map((entry) => (
                  <WatchlistRow
                    key={entry.symbol}
                    entry={entry}
                    onRemove={handleRemove}
                    onTierChange={handleTierChange}
                  />
                ))}
              </div>
            )}
          </>
        )}
      </main>

      {showAddModal && (
        <AddSymbolModal onClose={() => setShowAddModal(false)} onAdded={revisit} />
      )}
    </div>
  );
}
