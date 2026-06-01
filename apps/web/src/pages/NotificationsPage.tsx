import { Check, Trash2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../api/client";
import { PageHeader } from "../components/PageHeader";
import { EmptyState, ErrorState, LoadingState } from "../components/States";
import { useAuth } from "../state/AuthContext";
import type { Notification } from "../types";
import { formatDate } from "../utils/format";

export function NotificationsPage() {
  const { token } = useAuth();
  const [items, setItems] = useState<Notification[]>([]);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  const load = useCallback(async () => {
    if (!token) return;
    setIsLoading(true);
    try {
      setItems(await api.notifications(token));
      setError("");
    } catch {
      setError("Не удалось загрузить уведомления");
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  async function markRead(id: string) {
    if (!token) return;
    const updated = await api.markNotificationRead(id, token);
    setItems((current) => current.map((item) => (item.id === id ? updated : item)));
  }

  async function remove(id: string) {
    if (!token) return;
    await api.deleteNotification(id, token);
    setItems((current) => current.filter((item) => item.id !== id));
  }

  return (
    <>
      <PageHeader title="Уведомления" />
      {isLoading ? <LoadingState /> : null}
      {error ? <ErrorState message={error} /> : null}
      {!isLoading && !error && !items.length ? <EmptyState label="Уведомлений пока нет" /> : null}

      <div className="space-y-2">
        {items.map((item) => (
          <article
            key={item.id}
            className={[
              "rounded-lg border p-4 shadow-soft",
              item.isRead
                ? "border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900"
                : "border-teal-200 bg-teal-50 dark:border-teal-900 dark:bg-teal-950"
            ].join(" ")}
          >
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <div className="text-xs text-slate-500">{formatDate(item.createdAt)}</div>
                <h2 className="mt-1 font-semibold">{item.title}</h2>
                <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{item.message}</p>
                {item.entityId ? (
                  <Link className="mt-2 inline-flex text-sm font-medium text-teal-700" to="/tracked">
                    Открыть отслеживание
                  </Link>
                ) : null}
              </div>
              <div className="flex gap-2">
                {!item.isRead ? (
                  <button className="icon-button" onClick={() => markRead(item.id)} title="Прочитано" type="button">
                    <Check size={18} />
                  </button>
                ) : null}
                <button className="icon-button" onClick={() => remove(item.id)} title="Удалить" type="button">
                  <Trash2 size={18} />
                </button>
              </div>
            </div>
          </article>
        ))}
      </div>
    </>
  );
}
