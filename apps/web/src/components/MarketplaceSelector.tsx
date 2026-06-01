import { Check } from "lucide-react";

import type { Marketplace } from "../types";

type Props = {
  marketplaces: Marketplace[];
  selected: string[];
  onChange: (selected: string[]) => void;
};

export function MarketplaceSelector({ marketplaces, selected, onChange }: Props) {
  function toggle(id: string) {
    if (selected.includes(id)) {
      onChange(selected.filter((item) => item !== id));
      return;
    }
    onChange([...selected, id]);
  }

  return (
    <div className="grid gap-2 sm:grid-cols-2">
      {marketplaces.map((marketplace) => {
        const checked = selected.includes(marketplace.id);
        return (
          <button
            key={marketplace.id}
            className={[
              "flex h-14 items-center justify-between rounded-lg border px-4 text-left transition",
              checked
                ? "border-teal-600 bg-teal-50 text-teal-900 dark:border-teal-500 dark:bg-teal-950 dark:text-teal-100"
                : "border-slate-200 bg-white hover:border-slate-300 dark:border-slate-700 dark:bg-slate-900 dark:hover:border-slate-600"
            ].join(" ")}
            disabled={!marketplace.enabled}
            onClick={() => toggle(marketplace.id)}
            type="button"
          >
            <span>
              <span className="block text-sm font-semibold">{marketplace.name}</span>
              {marketplace.isMock ? <span className="text-xs text-slate-500">mock</span> : null}
            </span>
            <span
              className={[
                "grid h-6 w-6 place-items-center rounded-md border",
                checked ? "border-teal-600 bg-teal-600 text-white" : "border-slate-300 dark:border-slate-600"
              ].join(" ")}
            >
              {checked ? <Check size={15} /> : null}
            </span>
          </button>
        );
      })}
    </div>
  );
}
