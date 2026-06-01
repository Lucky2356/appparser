import { ArrowRight, ShoppingBag } from "lucide-react";
import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { ApiError } from "../api/client";
import { useAuth } from "../state/AuthContext";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);
    try {
      await login(email, password);
      navigate("/search");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось войти");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="grid min-h-screen bg-slate-50 px-4 py-8 dark:bg-slate-950">
      <section className="m-auto w-full max-w-md rounded-lg border border-slate-200 bg-white p-6 shadow-soft dark:border-slate-800 dark:bg-slate-900">
        <div className="mb-6 flex items-center gap-3">
          <div className="grid h-11 w-11 place-items-center rounded-lg bg-teal-700 text-white">
            <ShoppingBag size={21} />
          </div>
          <div>
            <h1 className="text-xl font-semibold">Appsparcer</h1>
            <p className="text-sm text-slate-500">Вход</p>
          </div>
        </div>

        <form className="space-y-4" onSubmit={handleSubmit}>
          <label className="block space-y-1 text-sm">
            <span className="text-slate-600 dark:text-slate-300">Email</span>
            <input className="input" required type="email" value={email} onChange={(event) => setEmail(event.target.value)} />
          </label>
          <label className="block space-y-1 text-sm">
            <span className="text-slate-600 dark:text-slate-300">Пароль</span>
            <input
              className="input"
              required
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>

          {error ? <div className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div> : null}

          <button className="primary-button w-full" disabled={isSubmitting} type="submit">
            Войти
            <ArrowRight size={18} />
          </button>
        </form>

        <div className="mt-4 text-center text-sm text-slate-500">
          <Link className="font-medium text-teal-700 hover:text-teal-800" to="/register">
            Создать аккаунт
          </Link>
        </div>
      </section>
    </main>
  );
}
