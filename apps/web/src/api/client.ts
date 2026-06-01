import type {
  AuthResponse,
  Favorite,
  Marketplace,
  Notification,
  ParserLog,
  PriceHistoryPoint,
  SearchCreate,
  SearchCreated,
  SearchItem,
  SearchResults,
  TrackedProduct,
  User
} from "../types";

const API_URL = import.meta.env.VITE_API_URL ?? "/api";

type RequestOptions = RequestInit & {
  token?: string | null;
};

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (options.token) {
    headers.set("Authorization", `Bearer ${options.token}`);
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers.get("content-type") ?? "";
  const payload = contentType.includes("application/json") ? await response.json() : await response.text();

  if (!response.ok) {
    const message = typeof payload === "object" && payload?.detail ? payload.detail : "Request failed";
    throw new ApiError(String(message), response.status);
  }

  return payload as T;
}

export const api = {
  register: (email: string, password: string) =>
    request<AuthResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password })
    }),

  login: (email: string, password: string) =>
    request<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password })
    }),

  me: (token: string) => request<User>("/auth/me", { token }),

  marketplaces: () => request<Marketplace[]>("/marketplaces"),

  createSearch: (payload: SearchCreate, token: string) =>
    request<SearchCreated>("/search", {
      method: "POST",
      token,
      body: JSON.stringify(payload)
    }),

  getSearch: (searchId: string, token: string) => request<SearchItem>(`/search/${searchId}`, { token }),

  getSearchResults: (searchId: string, token: string) =>
    request<SearchResults>(`/search/${searchId}/results`, { token }),

  getSearchLogs: (searchId: string, token: string) => request<ParserLog[]>(`/search/${searchId}/logs`, { token }),

  searchResultsCsvUrl: (searchId: string) => `${API_URL}/search/${searchId}/results.csv`,

  searchHistory: (token: string) => request<SearchItem[]>("/search/history", { token }),

  favorites: (token: string) => request<Favorite[]>("/favorites", { token }),

  addFavorite: (offerId: string, token: string) =>
    request<Favorite>("/favorites", {
      method: "POST",
      token,
      body: JSON.stringify({ offerId })
    }),

  deleteFavorite: (favoriteOrOfferId: string, token: string) =>
    request<void>(`/favorites/${favoriteOrOfferId}`, {
      method: "DELETE",
      token
    }),

  trackedProducts: (token: string) => request<TrackedProduct[]>("/tracked-products", { token }),

  createTrackedProduct: (
    payload: Omit<TrackedProduct, "id" | "createdAt">,
    token: string
  ) =>
    request<TrackedProduct>("/tracked-products", {
      method: "POST",
      token,
      body: JSON.stringify(payload)
    }),

  createTrackedFromOffer: (offerId: string, token: string, targetPrice?: number | null) =>
    request<TrackedProduct>("/tracked-products/from-offer", {
      method: "POST",
      token,
      body: JSON.stringify({ offerId, targetPrice: targetPrice ?? null })
    }),

  priceHistory: (trackedProductId: string, token: string) =>
    request<PriceHistoryPoint[]>(`/tracked-products/${trackedProductId}/price-history`, { token }),

  refreshTrackedProduct: (id: string, token: string) =>
    request<TrackedProduct>(`/tracked-products/${id}/refresh`, {
      method: "POST",
      token
    }),

  refreshAllTrackedProducts: (token: string) =>
    request<{ refreshed: number }>("/tracked-products/refresh-all", {
      method: "POST",
      token
    }),

  deleteTrackedProduct: (id: string, token: string) =>
    request<void>(`/tracked-products/${id}`, {
      method: "DELETE",
      token
    }),

  notifications: (token: string) => request<Notification[]>("/notifications", { token }),

  unreadNotifications: (token: string) => request<{ count: number }>("/notifications/unread-count", { token }),

  markNotificationRead: (id: string, token: string) =>
    request<Notification>(`/notifications/${id}/read`, {
      method: "POST",
      token
    }),

  deleteNotification: (id: string, token: string) =>
    request<void>(`/notifications/${id}`, {
      method: "DELETE",
      token
    })
};
