import { Navigate, Route, Routes } from "react-router-dom";

import { ProtectedLayout } from "./components/ProtectedLayout";
import { FavoritesPage } from "./pages/FavoritesPage";
import { HistoryPage } from "./pages/HistoryPage";
import { LoginPage } from "./pages/LoginPage";
import { NotificationsPage } from "./pages/NotificationsPage";
import { RegisterPage } from "./pages/RegisterPage";
import { ResultsPage } from "./pages/ResultsPage";
import { SearchPage } from "./pages/SearchPage";
import { SettingsPage } from "./pages/SettingsPage";
import { TrackedProductsPage } from "./pages/TrackedProductsPage";
import { useAuth } from "./state/AuthContext";

export function App() {
  const { token, isLoading } = useAuth();

  if (isLoading) {
    return <div className="grid min-h-screen place-items-center text-sm text-slate-500">Загрузка...</div>;
  }

  return (
    <Routes>
      <Route path="/login" element={token ? <Navigate to="/search" replace /> : <LoginPage />} />
      <Route path="/register" element={token ? <Navigate to="/search" replace /> : <RegisterPage />} />
      <Route element={token ? <ProtectedLayout /> : <Navigate to="/login" replace />}>
        <Route path="/" element={<Navigate to="/search" replace />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/results/:searchId" element={<ResultsPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/notifications" element={<NotificationsPage />} />
        <Route path="/favorites" element={<FavoritesPage />} />
        <Route path="/tracked" element={<TrackedProductsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>
      <Route path="*" element={<Navigate to={token ? "/search" : "/login"} replace />} />
    </Routes>
  );
}
