import type { User, WatchlistResponse, SymbolSearchResult, ConvictionTier } from "../types";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // ignore
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  signup: (email: string, password: string) =>
    request<User>("/auth/signup", { method: "POST", body: JSON.stringify({ email, password }) }),

  login: (email: string, password: string) =>
    request<User>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),

  logout: () => request<void>("/auth/logout", { method: "POST" }),

  me: () => request<User>("/auth/me"),

  getWatchlist: () => request<WatchlistResponse>("/watchlist"),

  getWatchlistLive: () => request<WatchlistResponse>("/watchlist/live"),

  searchSymbols: (q: string) =>
    request<SymbolSearchResult[]>(`/watchlist/search?q=${encodeURIComponent(q)}`),

  addSymbol: (symbol: string, conviction_tier: ConvictionTier) =>
    request<{ ok: true }>("/watchlist/items", {
      method: "POST",
      body: JSON.stringify({ symbol, conviction_tier }),
    }),

  removeSymbol: (symbol: string) =>
    request<{ ok: true }>(`/watchlist/items/${encodeURIComponent(symbol)}`, { method: "DELETE" }),

  updateTier: (symbol: string, conviction_tier: ConvictionTier) =>
    request<{ ok: true }>(`/watchlist/items/${encodeURIComponent(symbol)}`, {
      method: "PATCH",
      body: JSON.stringify({ conviction_tier }),
    }),
};

export { ApiError };
