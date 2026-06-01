import { Download, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { api, ApiError } from "../api/client";
import { PageHeader } from "../components/PageHeader";
import { ProductCard } from "../components/ProductCard";
import { EmptyState, ErrorState, LoadingState } from "../components/States";
import { useAuth } from "../state/AuthContext";
import type { Offer, ParserLog, SearchItem } from "../types";

export function ResultsPage() {
  const { searchId } = useParams();
  const { token } = useAuth();
  const [search, setSearch] = useState<SearchItem | null>(null);
  const [results, setResults] = useState<Offer[]>([]);
  const [logs, setLogs] = useState<ParserLog[]>([]);
  const [error, setError] = useState("");
  const [favoriteMessage, setFavoriteMessage] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  const load = useCallback(async () => {
    if (!token || !searchId) return;
    try {
      const [searchResponse, resultResponse, logsResponse] = await Promise.all([
        api.getSearch(searchId, token),
        api.getSearchResults(searchId, token),
        api.getSearchLogs(searchId, token)
      ]);
      setSearch(searchResponse);
      setResults(resultResponse.results);
      setLogs(logsResponse);
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
            {searchId && token ? (
              <a
                className="secondary-button"
                href={api.searchResultsCsvUrl(searchId)}
                onClick={(event) => {
                  event.preventDefault();
                  fetch(api.searchResultsCsvUrl(searchId), {
                    headers: { Authorization: `Bearer ${token}` }
                  })
                    .then((response) => response.blob())
                    .then((blob) => {
                      const url = URL.createObjectURL(blob);
                      const link = document.createElement("a");
                      link.href = url;
                      link.download = `search-${searchId}.csv`;
                      link.click();
                      URL.revokeObjectURL(url);
                    });
                }}
              >
                <Download size={17} />
                CSV
              </a>
            ) : null}
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
      {logs.length ? (
        <div className="mb-4 rounded-lg border border-slate-200 bg-white p-3 text-xs text-slate-500 dark:border-slate-800 dark:bg-slate-900">
          <div className="mb-2 font-semibold text-slate-700 dark:text-slate-200">Логи источников</div>
          <div className="flex flex-wrap gap-2">
            {logs.map((log) => (
              <span
                key={log.id}
                className="rounded-md border border-slate-200 px-2 py-1 dark:border-slate-700"
                title={new Date(log.createdAt).toLocaleString("ru-RU")}
              >
                {log.marketplace}: {log.message}
              </span>
            ))}
          </div>
        </div>
      ) : null}
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
