import { AlertTriangle, Loader2, SearchX } from "lucide-react";

export function LoadingState({ label = "Загрузка" }: { label?: string }) {
  return (
    <div className="flex min-h-48 items-center justify-center rounded-lg border border-dashed border-slate-300 bg-white text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-900">
      <Loader2 className="mr-2 animate-spin" size={18} />
      {label}
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="flex min-h-36 items-center justify-center rounded-lg border border-rose-200 bg-rose-50 px-4 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950 dark:text-rose-200">
      <AlertTriangle className="mr-2" size={18} />
      {message}
    </div>
  );
}

export function EmptyState({ label }: { label: string }) {
  return (
    <div className="flex min-h-40 items-center justify-center rounded-lg border border-dashed border-slate-300 bg-white px-4 text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-900">
      <SearchX className="mr-2" size={18} />
      {label}
    </div>
  );
}
