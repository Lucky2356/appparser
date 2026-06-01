import { Plus, RefreshCw, Trash2 } from "lucide-react";
import { FormEvent, useCallback, useEffect, useState } from "react";

import { api } from "../api/client";
import { PageHeader } from "../components/PageHeader";
import { PriceHistoryChart } from "../components/PriceHistoryChart";
import { EmptyState, ErrorState, LoadingState } from "../components/States";
import { useAuth } from "../state/AuthContext";
import type { PriceHistoryPoint, TrackedProduct } from "../types";
import { formatDate, formatPrice } from "../utils/format";

export function TrackedProductsPage() {
  const { token } = useAuth();
  const [items, setItems] = useState<TrackedProduct[]>([]);
  const [history, setHistory] = useState<Record<string, PriceHistoryPoint[]>>({});
  const [marketplace, setMarketplace] = useState("ozon");
  const [title, setTitle] = useState("");
  const [productUrl, setProductUrl] = useState("");
  const [targetPrice, setTargetPrice] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  const load = useCallback(async () => {
    if (!token) return;
    setIsLoading(true);
    try {
      const tracked = await api.trackedProducts(token);
      setItems(tracked);
      const entries = await Promise.all(
        tracked.map(async (item) => [item.id, await api.priceHistory(item.id, token)] as const)
      );
      setHistory(Object.fromEntries(entries));
      setError("");
    } catch {
      setError("Не удалось загрузить отслеживание");
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    try {
      const created = await api.createTrackedProduct(
        {
          marketplace,
          title,
          productUrl,
          targetPrice: targetPrice ? Number(targetPrice) : null,
          lastPrice: null
        },
        token
      );
      const points = await api.priceHistory(created.id, token);
      setItems((current) => [created, ...current]);
      setHistory((current) => ({ ...current, [created.id]: points }));
      setTitle("");
      setProductUrl("");
      setTargetPrice("");
      setError("");
    } catch {
      setError("Не удалось добавить товар");
    }
  }

  async function remove(id: string) {
    if (!token) return;
    await api.deleteTrackedProduct(id, token);
    setItems((current) => current.filter((item) => item.id !== id));
    setHistory((current) => {
      const next = { ...current };
      delete next[id];
      return next;
    });
  }

  async function refresh(id: string) {
    if (!token) return;
    const updated = await api.refreshTrackedProduct(id, token);
    const points = await api.priceHistory(id, token);
    setItems((current) => current.map((item) => (item.id === id ? updated : item)));
    setHistory((current) => ({ ...current, [id]: points }));
  }

  return (
    <>
      <PageHeader title="Отслеживание" />

      <form
        className="mb-5 grid gap-3 rounded-lg border border-slate-200 bg-white p-4 shadow-soft dark:border-slate-800 dark:bg-slate-900 lg:grid-cols-[160px_1fr_1.4fr_160px_auto]"
        onSubmit={handleSubmit}
      >
        <select className="input" value={marketplace} onChange={(event) => setMarketplace(event.target.value)}>
          <option value="ozon">Ozon</option>
          <option value="wildberries">Wildberries</option>
        </select>
        <input
          className="input"
          placeholder="Название"
          required
          value={title}
          onChange={(event) => setTitle(event.target.value)}
        />
        <input
          className="input"
          placeholder="Ссылка"
          required
          value={productUrl}
          onChange={(event) => setProductUrl(event.target.value)}
        />
        <input
          className="input"
          min="0"
          placeholder="Цель"
          step="100"
          type="number"
          value={targetPrice}
          onChange={(event) => setTargetPrice(event.target.value)}
        />
        <button className="primary-button" type="submit">
          <Plus size={18} />
          Добавить
        </button>
      </form>

      {isLoading ? <LoadingState /> : null}
      {error ? <ErrorState message={error} /> : null}
      {!isLoading && !error && !items.length ? <EmptyState label="Товары для отслеживания не добавлены" /> : null}

      <div className="space-y-2">
        {items.map((item) => (
          <article
            key={item.id}
            className="rounded-lg border border-slate-200 bg-white p-4 shadow-soft dark:border-slate-800 dark:bg-slate-900"
          >
            <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div className="min-w-0">
                <h2 className="truncate font-semibold">{item.title}</h2>
                <div className="mt-1 flex flex-wrap gap-2 text-xs text-slate-500">
                  <span>{item.marketplace}</span>
                  <span>{formatDate(item.createdAt)}</span>
                  {item.lastPrice ? <span>сейчас {formatPrice(item.lastPrice)}</span> : null}
                  {item.targetPrice ? <span>цель {formatPrice(item.targetPrice)}</span> : null}
                </div>
                <PriceHistoryChart points={history[item.id] ?? []} />
              </div>
              <div className="flex gap-2">
                <button className="icon-button" onClick={() => refresh(item.id)} title="Обновить цену" type="button">
                  <RefreshCw size={18} />
                </button>
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
