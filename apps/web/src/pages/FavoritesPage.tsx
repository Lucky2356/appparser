import { Trash2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { api } from "../api/client";
import { PageHeader } from "../components/PageHeader";
import { ProductCard } from "../components/ProductCard";
import { EmptyState, ErrorState, LoadingState } from "../components/States";
import { useAuth } from "../state/AuthContext";
import type { Favorite } from "../types";

export function FavoritesPage() {
  const { token } = useAuth();
  const [items, setItems] = useState<Favorite[]>([]);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  const load = useCallback(async () => {
    if (!token) return;
    setIsLoading(true);
    try {
      const response = await api.favorites(token);
      setItems(response);
      setError("");
    } catch {
      setError("Не удалось загрузить избранное");
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  async function remove(id: string) {
    if (!token) return;
    await api.deleteFavorite(id, token);
    setItems((current) => current.filter((item) => item.id !== id));
  }

  return (
    <>
      <PageHeader title="Избранное" />
      {isLoading ? <LoadingState /> : null}
      {error ? <ErrorState message={error} /> : null}
      {!isLoading && !error && !items.length ? <EmptyState label="Избранных товаров пока нет" /> : null}

      <div className="space-y-3">
        {items.map((item) => (
          <div key={item.id} className="relative">
            <ProductCard offer={item} />
            <button
              className="absolute right-16 top-6 grid h-9 w-9 place-items-center rounded-md border border-slate-200 bg-white text-slate-500 hover:text-rose-600 dark:border-slate-700 dark:bg-slate-900"
              onClick={() => remove(item.id)}
              title="Удалить"
              type="button"
            >
              <Trash2 size={17} />
            </button>
          </div>
        ))}
      </div>
    </>
  );
}
