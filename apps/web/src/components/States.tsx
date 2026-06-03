import { AlertTriangle, Loader2, SearchX } from "lucide-react";

export function LoadingState({ label = "Загрузка" }: { label?: string }) {
  return (
    <div className="flex min-h-48 items-center justify-center rounded-lg border border-dashed border-slate-300 bg-white/80 text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-900/80">
      <div className="flex items-center rounded-md bg-white px-3 py-2 shadow-sm dark:bg-slate-900">
        <Loader2 className="mr-2 animate-spin text-teal-700 dark:text-teal-300" size={18} />
        {label}
      </div>
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="flex min-h-36 items-center justify-center rounded-lg border border-rose-200 bg-rose-50 px-4 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950 dark:text-rose-200">
      <div className="flex max-w-2xl items-center gap-2">
        <AlertTriangle className="shrink-0" size={18} />
        <span>{message}</span>
      </div>
    </div>
  );
}

export function EmptyState({ label }: { label: string }) {
  return (
    <div className="grid min-h-40 place-items-center rounded-lg border border-dashed border-slate-300 bg-white px-4 text-center text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-900">
      <div>
        <SearchX className="mx-auto mb-2 text-slate-400" size={22} />
        {label}
      </div>
    </div>
  );
}
