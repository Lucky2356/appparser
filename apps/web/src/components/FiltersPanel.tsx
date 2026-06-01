import type { SearchFilters } from "../types";

type Props = {
  filters: SearchFilters;
  onChange: (filters: SearchFilters) => void;
  sort: string;
  onSortChange: (sort: string) => void;
};

export function FiltersPanel({ filters, onChange, sort, onSortChange }: Props) {
  const setNumber = (key: keyof SearchFilters, value: string) => {
    onChange({ ...filters, [key]: value === "" ? null : Number(value) });
  };

  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
      <label className="space-y-1 text-sm">
        <span className="text-slate-600 dark:text-slate-300">Рейтинг от</span>
        <input
          className="input"
          max="5"
          min="0"
          step="0.1"
          type="number"
          value={filters.minRating ?? ""}
          onChange={(event) => setNumber("minRating", event.target.value)}
        />
      </label>
      <label className="space-y-1 text-sm">
        <span className="text-slate-600 dark:text-slate-300">Отзывы от</span>
        <input
          className="input"
          min="0"
          step="1"
          type="number"
          value={filters.minReviews ?? ""}
          onChange={(event) => setNumber("minReviews", event.target.value)}
        />
      </label>
      <label className="space-y-1 text-sm">
        <span className="text-slate-600 dark:text-slate-300">Цена от</span>
        <input
          className="input"
          min="0"
          step="100"
          type="number"
          value={filters.minPrice ?? ""}
          onChange={(event) => setNumber("minPrice", event.target.value)}
        />
      </label>
      <label className="space-y-1 text-sm">
        <span className="text-slate-600 dark:text-slate-300">Цена до</span>
        <input
          className="input"
          min="0"
          step="100"
          type="number"
          value={filters.maxPrice ?? ""}
          onChange={(event) => setNumber("maxPrice", event.target.value)}
        />
      </label>
      <label className="space-y-1 text-sm">
        <span className="text-slate-600 dark:text-slate-300">Сортировка</span>
        <select className="input" value={sort} onChange={(event) => onSortChange(event.target.value)}>
          <option value="best_value">Выгодность</option>
          <option value="price_asc">Цена</option>
          <option value="rating_desc">Рейтинг</option>
        </select>
      </label>
    </div>
  );
}
