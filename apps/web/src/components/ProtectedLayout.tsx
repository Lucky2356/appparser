import {
  Clock3,
  Heart,
  LogOut,
  Moon,
  Search,
  Settings,
  ShoppingBag,
  Sun,
  Target
} from "lucide-react";
import { useEffect, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../state/AuthContext";

const navItems = [
  { to: "/search", label: "Поиск", icon: Search },
  { to: "/history", label: "История", icon: Clock3 },
  { to: "/favorites", label: "Избранное", icon: Heart },
  { to: "/tracked", label: "Отслеживание", icon: Target },
  { to: "/settings", label: "Настройки", icon: Settings }
];

export function ProtectedLayout() {
  const { user, logout } = useAuth();
  const [isDark, setIsDark] = useState(() => localStorage.getItem("appsparcer.theme") === "dark");

  useEffect(() => {
    document.documentElement.classList.toggle("dark", isDark);
    localStorage.setItem("appsparcer.theme", isDark ? "dark" : "light");
  }, [isDark]);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-950 dark:bg-slate-950 dark:text-slate-100">
      <aside className="fixed inset-y-0 left-0 z-20 hidden w-64 border-r border-slate-200 bg-white px-4 py-5 dark:border-slate-800 dark:bg-slate-900 lg:block">
        <div className="flex items-center gap-3 px-2">
          <div className="grid h-10 w-10 place-items-center rounded-lg bg-teal-700 text-white">
            <ShoppingBag size={20} />
          </div>
          <div>
            <div className="font-semibold tracking-normal">Appsparcer</div>
            <div className="text-xs text-slate-500">{user?.email}</div>
          </div>
        </div>

        <nav className="mt-8 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                [
                  "flex h-11 items-center gap-3 rounded-md px-3 text-sm font-medium transition",
                  isActive
                    ? "bg-teal-50 text-teal-800 dark:bg-teal-950 dark:text-teal-200"
                    : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                ].join(" ")
              }
            >
              <item.icon size={18} />
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="absolute inset-x-4 bottom-5 space-y-2">
          <button
            className="flex h-10 w-full items-center justify-center gap-2 rounded-md border border-slate-200 text-sm hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"
            onClick={() => setIsDark((value) => !value)}
            type="button"
          >
            {isDark ? <Sun size={17} /> : <Moon size={17} />}
            {isDark ? "Светлая тема" : "Тёмная тема"}
          </button>
          <button
            className="flex h-10 w-full items-center justify-center gap-2 rounded-md bg-slate-900 text-sm text-white hover:bg-slate-800 dark:bg-slate-100 dark:text-slate-950"
            onClick={logout}
            type="button"
          >
            <LogOut size={17} />
            Выйти
          </button>
        </div>
      </aside>

      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/95 px-4 py-3 backdrop-blur dark:border-slate-800 dark:bg-slate-900/95 lg:hidden">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 font-semibold">
            <ShoppingBag size={20} className="text-teal-700" />
            Appsparcer
          </div>
          <button className="rounded-md p-2 hover:bg-slate-100 dark:hover:bg-slate-800" onClick={logout} type="button">
            <LogOut size={18} />
          </button>
        </div>
        <nav className="mt-3 grid grid-cols-5 gap-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                [
                  "grid h-10 place-items-center rounded-md",
                  isActive ? "bg-teal-50 text-teal-800 dark:bg-teal-950 dark:text-teal-200" : "text-slate-500"
                ].join(" ")
              }
              title={item.label}
            >
              <item.icon size={18} />
            </NavLink>
          ))}
        </nav>
      </header>

      <main className="lg:pl-64">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
