import { useEffect, useState } from "react";
import { api, ApiError } from "../api/client";
import type { AlertRule, AlertRuleType } from "../types";

const TYPE_LABELS: Record<AlertRuleType, string> = {
  price_above: "Price above",
  price_below: "Price below",
  volume_multiple: "Volume spikes past",
};

export default function AlertsSection({ symbol }: { symbol: string }) {
  const [alerts, setAlerts] = useState<AlertRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [ruleType, setRuleType] = useState<AlertRuleType>("price_above");
  const [threshold, setThreshold] = useState("");
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    api.listAlerts(symbol).then(setAlerts).catch(() => {}).finally(() => setLoading(false));
  };

  useEffect(load, [symbol]);

  const handleCreate = async () => {
    const value = parseFloat(threshold);
    if (!value || value <= 0) { setError("Enter a valid number"); return; }
    setError(null);
    try {
      await api.createAlert(symbol, ruleType, value);
      setThreshold("");
      setShowForm(false);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create alert");
    }
  };

  const handleDelete = async (id: number) => {
    await api.deleteAlert(symbol, id);
    load();
  };

  if (loading) return null;

  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-[11px] text-slate-500">Custom alerts</span>
        <button onClick={() => setShowForm((s) => !s)} className="text-[11px] text-emerald-400 hover:underline">
          {showForm ? "Cancel" : "+ Add alert"}
        </button>
      </div>

      {alerts.length > 0 && (
        <div className="space-y-1 mb-2">
          {alerts.map((a) => (
            <div key={a.id} className={`flex items-center justify-between text-xs rounded-lg px-2.5 py-1.5 ${a.triggered_at ? "bg-emerald-500/10 text-emerald-300" : "bg-white/[0.03] text-slate-400"}`}>
              <span>
                {TYPE_LABELS[a.rule_type]} {a.rule_type === "volume_multiple" ? `${a.threshold}x` : `₹${a.threshold}`}
                {a.triggered_at && " — triggered"}
              </span>
              <button onClick={() => handleDelete(a.id)} className="text-slate-600 hover:text-rose-400">✕</button>
            </div>
          ))}
        </div>
      )}

      {showForm && (
        <div className="flex items-center gap-2 flex-wrap">
          <select
            value={ruleType} onChange={(e) => setRuleType(e.target.value as AlertRuleType)}
            className="text-xs bg-[#0a0e14] border border-white/10 rounded-lg px-2 py-1.5 text-white"
          >
            <option value="price_above">Price above</option>
            <option value="price_below">Price below</option>
            <option value="volume_multiple">Volume spikes past (x avg)</option>
          </select>
          <input
            type="number" value={threshold} onChange={(e) => setThreshold(e.target.value)}
            placeholder={ruleType === "volume_multiple" ? "e.g. 3" : "e.g. 1500"}
            className="text-xs bg-[#0a0e14] border border-white/10 rounded-lg px-2 py-1.5 text-white w-24 placeholder:text-slate-600"
          />
          <button onClick={handleCreate} className="text-xs px-2.5 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-medium">
            Set
          </button>
        </div>
      )}
      {error && <p className="text-[11px] text-rose-400 mt-1">{error}</p>}
      {!showForm && alerts.length === 0 && <p className="text-[11px] text-slate-600">No custom alerts set.</p>}
    </div>
  );
}
