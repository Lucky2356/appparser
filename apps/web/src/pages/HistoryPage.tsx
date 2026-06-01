import { ExternalLink } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../api/client";
import { PageHeader } from "../components/PageHeader";
import { EmptyState, ErrorState, LoadingState } from "../components/States";
import { useAuth } from "../state/AuthContext";
import type { SearchItem } from "../types";
import { formatDate } from "../utils/format";

export function HistoryPage() {
  const { token } = useAuth();
  const [items, setItems] = useState<SearchItem[]>([]);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    api
      .searchHistory(token)
      .then(setItems)
      .catch(() => setError("Не удалось загрузить историю"))
      .finally(() => setIsLoading(false));
  }, [token]);

  return (
    <>
      <PageHeader title="История" />
      {isLoading ? <LoadingState /> : null}
      {error ? <ErrorState message={error} /> : null}
      {!isLoading && !error && !items.length ? <EmptyState label="История поиска пустая" /> : null}

      <div className="space-y-2">
        {items.map((item) => (
          <article
            key={item.id}
            className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-white p-4 shadow-soft dark:border-slate-800 dark:bg-slate-900 sm:flex-row sm:items-center sm:justify-between"
          >
            <div>
              <h2 className="font-semibold">{item.query}</h2>
              <div className="mt-1 flex flex-wrap gap-2 text-xs text-slate-500">
                <span>{formatDate(item.createdAt)}</span>
                <span>{item.marketplaces.join(", ")}</span>
                <span>{item.status}</span>
              </div>
            </div>
            <Link className="secondary-button sm:w-auto" to={`/results/${item.id}`}>
              <ExternalLink size={17} />
              Открыть
            </Link>
          </article>
        ))}
      </div>
    </>
  );
}
