import { Database, Server, ShieldCheck } from "lucide-react";

import { PageHeader } from "../components/PageHeader";

const items = [
  { icon: Server, label: "API", value: "FastAPI" },
  { icon: Database, label: "Очередь", value: "Celery + Redis" },
  { icon: ShieldCheck, label: "Авторизация", value: "JWT" }
];

export function SettingsPage() {
  return (
    <>
      <PageHeader title="Настройки" />
      <div className="grid gap-3 md:grid-cols-3">
        {items.map((item) => (
          <article
            key={item.label}
            className="rounded-lg border border-slate-200 bg-white p-4 shadow-soft dark:border-slate-800 dark:bg-slate-900"
          >
            <div className="mb-4 grid h-10 w-10 place-items-center rounded-md bg-cyan-50 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-200">
              <item.icon size={20} />
            </div>
            <div className="text-sm text-slate-500">{item.label}</div>
            <div className="mt-1 font-semibold">{item.value}</div>
          </article>
        ))}
      </div>
    </>
  );
}
