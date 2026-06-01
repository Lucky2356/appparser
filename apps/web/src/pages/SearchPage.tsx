import { Search } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { api, ApiError } from "../api/client";
import { FiltersPanel } from "../components/FiltersPanel";
import { MarketplaceSelector } from "../components/MarketplaceSelector";
import { PageHeader } from "../components/PageHeader";
import { ErrorState, LoadingState } from "../components/States";
import { useAuth } from "../state/AuthContext";
import type { Marketplace, SearchFilters } from "../types";

export function SearchPage() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [query, setQuery] = useState("Телефон Samsung");
  const [marketplaces, setMarketplaces] = useState<Marketplace[]>([]);
  const [selected, setSelected] = useState<string[]>(["ozon", "wildberries"]);
  const [filters, setFilters] = useState<SearchFilters>({ minRating: 4.7, minReviews: 100, maxPrice: 50000 });
  const [sort, setSort] = useState("best_value");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    api
      .marketplaces()
      .then((items) => {
        if (!cancelled) {
          setMarketplaces(items);
          setSelected(items.filter((item) => item.enabled).map((item) => item.id));
        }
      })
      .catch(() => setError("Не удалось загрузить маркетплейсы"))
      .finally(() => {
        if (!cancelled) {
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    setError("");
    setIsSubmitting(true);

    try {
      const response = await api.createSearch(
        {
          query,
          marketplaces: selected,
          filters,
          sort
        },
        token
      );
      navigate(`/results/${response.searchId}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось запустить поиск");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <>
      <PageHeader title="Поиск" />

      {isLoading ? (
        <LoadingState />
      ) : (
        <form className="space-y-5" onSubmit={handleSubmit}>
          <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-soft dark:border-slate-800 dark:bg-slate-900">
            <label className="block space-y-2">
              <span className="text-sm font-medium text-slate-600 dark:text-slate-300">Товар</span>
              <div className="flex flex-col gap-2 sm:flex-row">
                <input
                  className="input h-12 text-base"
                  minLength={2}
                  required
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                />
                <button className="primary-button h-12 sm:w-44" disabled={isSubmitting || !selected.length} type="submit">
                  <Search size={18} />
                  Найти
                </button>
              </div>
            </label>
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-soft dark:border-slate-800 dark:bg-slate-900">
            <div className="mb-3 text-sm font-medium text-slate-600 dark:text-slate-300">Маркетплейсы</div>
            <MarketplaceSelector marketplaces={marketplaces} selected={selected} onChange={setSelected} />
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-soft dark:border-slate-800 dark:bg-slate-900">
            <div className="mb-3 text-sm font-medium text-slate-600 dark:text-slate-300">Фильтры</div>
            <FiltersPanel filters={filters} sort={sort} onChange={setFilters} onSortChange={setSort} />
          </section>

          {error ? <ErrorState message={error} /> : null}
        </form>
      )}
    </>
  );
}
