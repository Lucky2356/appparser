import type { PriceHistoryPoint } from "../types";
import { formatPrice } from "../utils/format";

export function PriceHistoryChart({ points }: { points: PriceHistoryPoint[] }) {
  if (!points.length) {
    return <div className="text-xs text-slate-500">История цен появится после первого обновления</div>;
  }

  const prices = points.map((point) => point.price);
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const range = Math.max(1, max - min);

  return (
    <div className="mt-3">
      <div className="mb-2 flex justify-between text-xs text-slate-500">
        <span>{formatPrice(min)}</span>
        <span>{formatPrice(max)}</span>
      </div>
      <div className="flex h-16 items-end gap-1 rounded-md border border-slate-200 bg-slate-50 p-2 dark:border-slate-700 dark:bg-slate-950">
        {points.slice(-16).map((point) => {
          const height = 20 + ((point.price - min) / range) * 72;
          return (
            <div
              key={point.id}
              className="min-w-2 flex-1 rounded-sm bg-teal-600 dark:bg-teal-400"
              style={{ height: `${height}%` }}
              title={`${formatPrice(point.price)} · ${new Date(point.collectedAt).toLocaleString("ru-RU")}`}
            />
          );
        })}
      </div>
    </div>
  );
}
