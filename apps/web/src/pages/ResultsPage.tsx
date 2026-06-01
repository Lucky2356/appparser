import { RefreshCw } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { api, ApiError } from "../api/client";
import { PageHeader } from "../components/PageHeader";
import { ProductCard } from "../components/ProductCard";
import { EmptyState, ErrorState, LoadingState } from "../components/States";
import { useAuth } from "../state/AuthContext";
import type { Offer, SearchItem } from "../types";

export function ResultsPage() {
  const { searchId } = useParams();
  const { token } = useAuth();
  const [search, setSearch] = useState<SearchItem | null>(null);
  const [results, setResults] = useState<Offer[]>([]);
  const [error, setError] = useState("");
  const [favoriteMessage, setFavoriteMessage] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  const load = useCallback(async () => {
    if (!token || !searchId) return;
    try {
      const [searchResponse, resultResponse] = await Promise.all([
        api.getSearch(searchId, token),
        api.getSearchResults(searchId, token)
      ]);
      setSearch(searchResponse);
      setResults(resultResponse.results);
      setError(searchResponse.status === "failed" ? searchResponse.error ?? "Поиск завершился ошибкой" : "");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось загрузить результаты");
    } finally {
      setIsLoading(false);
    }
  }, [searchId, token]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (!search || search.status !== "processing") return;
    const timer = window.setTimeout(load, 1500);
    return () => window.clearTimeout(timer);
  }, [load, search]);

  async function addFavorite(offerId: string) {
    if (!token) return;
    setFavoriteMessage("");
    try {
      await api.addFavorite(offerId, token);
      setFavoriteMessage("Сохранено в избранное");
    } catch (err) {
      setFavoriteMessage(err instanceof ApiError ? err.message : "Не удалось сохранить");
    }
  }

  async function trackOffer(offerId: string) {
    if (!token) return;
    setFavoriteMessage("");
    try {
      await api.createTrackedFromOffer(offerId, token);
      setFavoriteMessage("Товар добавлен в отслеживание");
    } catch (err) {
      setFavoriteMessage(err instanceof ApiError ? err.message : "Не удалось добавить отслеживание");
    }
  }

  return (
    <>
      <PageHeader
        title="Результаты"
        actions={
          <>
            <button className="secondary-button" onClick={load} type="button">
              <RefreshCw size={17} />
              Обновить
            </button>
            <Link className="primary-button" to="/search">
              Новый поиск
            </Link>
          </>
        }
      />

      {search ? (
        <div className="mb-4 flex flex-wrap items-center gap-2 text-sm text-slate-500">
          <span className="rounded-md bg-slate-100 px-2 py-1 dark:bg-slate-800">{search.query}</span>
          <span className="rounded-md bg-slate-100 px-2 py-1 dark:bg-slate-800">{search.status}</span>
          {favoriteMessage ? <span className="rounded-md bg-emerald-50 px-2 py-1 text-emerald-700">{favoriteMessage}</span> : null}
        </div>
      ) : null}

      {isLoading ? <LoadingState label="Получаем результаты" /> : null}
      {error ? <ErrorState message={error} /> : null}
      {!isLoading && !error && search?.status === "processing" ? <LoadingState label="Поиск выполняется" /> : null}
      {!isLoading && !error && search?.status === "completed" && results.length === 0 ? (
        <EmptyState label="Подходящих предложений не найдено" />
      ) : null}

      <div className="space-y-3">
        {results.map((offer) => (
          <ProductCard key={offer.id} offer={offer} onFavorite={addFavorite} onTrack={trackOffer} />
        ))}
      </div>
    </>
  );
}
