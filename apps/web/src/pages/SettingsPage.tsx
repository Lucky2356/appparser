import { Bell, Database, Save, Send, Server, ShieldCheck } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";

import { api } from "../api/client";
import { PageHeader } from "../components/PageHeader";
import { ErrorState, LoadingState } from "../components/States";
import { useAuth } from "../state/AuthContext";

const items = [
  { icon: Server, label: "API", value: "FastAPI" },
  { icon: Database, label: "Очередь", value: "Celery + Redis" },
  { icon: ShieldCheck, label: "Авторизация", value: "JWT" }
];

export function SettingsPage() {
  const { token } = useAuth();
  const [telegramChatId, setTelegramChatId] = useState("");
  const [telegramEnabled, setTelegramEnabled] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    api
      .settings(token)
      .then((settings) => {
        setTelegramChatId(settings.telegramChatId ?? "");
        setTelegramEnabled(settings.telegramNotificationsEnabled);
      })
      .catch(() => setError("Не удалось загрузить настройки"))
      .finally(() => setIsLoading(false));
  }, [token]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    setMessage("");
    setError("");
    try {
      const settings = await api.updateSettings(
        {
          telegramChatId: telegramChatId.trim() || null,
          telegramNotificationsEnabled: telegramEnabled
        },
        token
      );
      setTelegramChatId(settings.telegramChatId ?? "");
      setTelegramEnabled(settings.telegramNotificationsEnabled);
      setMessage("Настройки сохранены");
    } catch {
      setError("Не удалось сохранить настройки");
    }
  }

  async function handleTestTelegram() {
    if (!token) return;
    setMessage("");
    setError("");
    try {
      const response = await api.testTelegram(token);
      if (response.sent) {
        setMessage(response.message);
      } else {
        setError(response.message);
      }
    } catch {
      setError("Не удалось выполнить тестовую отправку");
    }
  }

  return (
    <>
      <PageHeader title="Настройки" />
      <div className="grid gap-3 md:grid-cols-3">
        {items.map((item) => (
          <article
            key={item.label}
            className="rounded-lg border border-slate-200 bg-white p-4 shadow-soft dark:border-slate-800 dark:bg-slate-900"
          >
            <div className="mb-4 grid h-10 w-10 place-items-center rounded-md bg-cyan-50 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-200">
              <item.icon size={20} />
            </div>
            <div className="text-sm text-slate-500">{item.label}</div>
            <div className="mt-1 font-semibold">{item.value}</div>
          </article>
        ))}
      </div>

      <section className="mt-5 rounded-lg border border-slate-200 bg-white p-4 shadow-soft dark:border-slate-800 dark:bg-slate-900">
        <div className="mb-4 flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-md bg-teal-50 text-teal-700 dark:bg-teal-950 dark:text-teal-200">
            <Send size={20} />
          </div>
          <div>
            <h2 className="font-semibold">Telegram-уведомления</h2>
            <div className="text-sm text-slate-500">Снижение цены и достижение целевой цены</div>
          </div>
        </div>

        {isLoading ? (
          <LoadingState />
        ) : (
          <form className="grid gap-3 md:grid-cols-[1fr_auto]" onSubmit={handleSubmit}>
            <label className="space-y-1 text-sm">
              <span className="text-slate-600 dark:text-slate-300">Telegram chat ID</span>
              <input
                className="input"
                placeholder="123456789"
                value={telegramChatId}
                onChange={(event) => setTelegramChatId(event.target.value)}
              />
            </label>
            <label className="flex h-10 items-center gap-2 self-end rounded-md border border-slate-300 px-3 text-sm dark:border-slate-700">
              <input
                checked={telegramEnabled}
                className="h-4 w-4"
                type="checkbox"
                onChange={(event) => setTelegramEnabled(event.target.checked)}
              />
              <Bell size={16} />
              Включить
            </label>
            <button className="primary-button md:w-44" type="submit">
              <Save size={18} />
              Сохранить
            </button>
            <button className="secondary-button md:w-44" type="button" onClick={handleTestTelegram}>
              <Send size={18} />
              Тест
            </button>
          </form>
        )}

        {message ? <div className="mt-3 rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{message}</div> : null}
        {error ? <div className="mt-3"><ErrorState message={error} /></div> : null}
      </section>
    </>
  );
}
