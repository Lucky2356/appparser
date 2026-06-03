import { Search, SlidersHorizontal, Sparkles, Store } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { api, ApiError } from "../api/client";
import { FiltersPanel } from "../components/FiltersPanel";
import { MarketplaceSelector } from "../components/MarketplaceSelector";
import { PageHeader } from "../components/PageHeader";
import { ErrorState, LoadingState } from "../components/States";
import { useAuth } from "../state/AuthContext";
import type { Marketplace, SearchFilters } from "../types";

const quickQueries = ["iphone", "ноутбук", "пылесос", "кроссовки", "кофемашина"];

export function SearchPage() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [query, setQuery] = useState("Телефон Samsung");
  const [marketplaces, setMarketplaces] = useState<Marketplace[]>([]);
  const [selected, setSelected] = useState<string[]>(["ozon", "wildberries"]);
  const [filters, setFilters] = useState<SearchFilters>({});
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
          <section className="surface p-5">
            <label className="block space-y-2">
              <span className="section-label flex items-center gap-2">
                <Sparkles size={16} className="text-teal-700 dark:text-teal-300" />
                Товар
              </span>
              <div className="flex flex-col gap-2 sm:flex-row">
                <input
                  className="input h-12 text-base"
                  minLength={2}
                  placeholder="Название, бренд или модель"
                  required
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                />
                <button className="primary-button h-12 sm:w-44" disabled={isSubmitting || !selected.length} type="submit">
                  <Search size={18} />
                  {isSubmitting ? "Ищем" : "Найти"}
                </button>
              </div>
            </label>
            <div className="mt-3 flex flex-wrap gap-2">
              {quickQueries.map((item) => (
                <button
                  key={item}
                  className="subtle-chip transition hover:border-teal-300 hover:text-teal-700 dark:hover:border-teal-700 dark:hover:text-teal-200"
                  onClick={() => setQuery(item)}
                  type="button"
                >
                  {item}
                </button>
              ))}
            </div>
          </section>

          <section className="surface p-5">
            <div className="mb-3 flex items-center justify-between gap-3">
              <div className="section-label flex items-center gap-2">
                <Store size={16} className="text-teal-700 dark:text-teal-300" />
                Маркетплейсы
              </div>
              <div className="text-xs text-slate-500">{selected.length} выбрано</div>
            </div>
            <MarketplaceSelector marketplaces={marketplaces} selected={selected} onChange={setSelected} />
          </section>

          <section className="surface p-5">
            <div className="mb-3 section-label flex items-center gap-2">
              <SlidersHorizontal size={16} className="text-teal-700 dark:text-teal-300" />
              Фильтры
            </div>
            <FiltersPanel filters={filters} sort={sort} onChange={setFilters} onSortChange={setSort} />
          </section>

          {error ? <ErrorState message={error} /> : null}
        </form>
      )}
    </>
  );
}
