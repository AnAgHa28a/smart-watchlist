import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth, ApiError } from "../hooks/useAuth";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthShell>
      <h1 className="text-2xl font-semibold text-white mb-1">Welcome back</h1>
      <p className="text-sm text-slate-400 mb-8">Log in to see what's changed.</p>
      <form onSubmit={handleSubmit} className="space-y-4">
        <Field label="Email">
          <input
            type="email" required autoFocus value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={inputCls}
            placeholder="you@example.com"
          />
        </Field>
        <Field label="Password">
          <input
            type="password" required value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={inputCls}
            placeholder="••••••••"
          />
        </Field>
        {error && <p className="text-sm text-rose-400">{error}</p>}
        <button
          type="submit" disabled={submitting}
          className="w-full rounded-lg bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-slate-950 font-medium py-2.5 transition-colors"
        >
          {submitting ? "Logging in…" : "Log in"}
        </button>
      </form>
      <p className="text-sm text-slate-400 mt-6 text-center">
        No account? <Link to="/signup" className="text-emerald-400 hover:underline">Sign up</Link>
      </p>
    </AuthShell>
  );
}

export function AuthShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0a0e14] px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex items-center gap-2 justify-center">
          <div className="h-8 w-8 rounded-lg bg-emerald-500 flex items-center justify-center text-slate-950 font-bold">S</div>
          <span className="text-white font-semibold text-lg">Signal</span>
        </div>
        <div className="bg-[#111826] border border-white/5 rounded-2xl p-8 shadow-2xl">
          {children}
        </div>
      </div>
    </div>
  );
}

export function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="block text-xs font-medium text-slate-400 mb-1.5">{label}</span>
      {children}
    </label>
  );
}

export const inputCls =
  "w-full rounded-lg bg-[#0a0e14] border border-white/10 focus:border-emerald-500 focus:outline-none px-3 py-2.5 text-sm text-white placeholder:text-slate-600 transition-colors";
