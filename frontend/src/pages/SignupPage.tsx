import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth, ApiError } from "../hooks/useAuth";
import { AuthShell, Field, inputCls } from "./LoginPage";

export default function SignupPage() {
  const { signup } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    if (password.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }
    setSubmitting(true);
    try {
      await signup(email, password);
      navigate("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthShell>
      <h1 className="text-2xl font-semibold text-white mb-1">Create your account</h1>
      <p className="text-sm text-slate-400 mb-8">Your watchlist follows you across devices.</p>
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
            placeholder="At least 6 characters"
          />
        </Field>
        {error && <p className="text-sm text-rose-400">{error}</p>}
        <button
          type="submit" disabled={submitting}
          className="w-full rounded-lg bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-slate-950 font-medium py-2.5 transition-colors"
        >
          {submitting ? "Creating account…" : "Sign up"}
        </button>
      </form>
      <p className="text-sm text-slate-400 mt-6 text-center">
        Already have an account? <Link to="/login" className="text-emerald-400 hover:underline">Log in</Link>
      </p>
    </AuthShell>
  );
}
