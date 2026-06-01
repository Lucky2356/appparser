export type User = {
  id: string;
  email: string;
};

export type AuthResponse = {
  accessToken: string;
  tokenType: string;
  user: User;
};

export type Marketplace = {
  id: string;
  name: string;
  enabled: boolean;
  isMock: boolean;
};

export type SearchFilters = {
  minRating?: number | null;
  minReviews?: number | null;
  minPrice?: number | null;
  maxPrice?: number | null;
};

export type SearchCreate = {
  query: string;
  marketplaces: string[];
  filters: SearchFilters;
  sort: string;
};

export type SearchCreated = {
  searchId: string;
  status: string;
};

export type SearchItem = {
  id: string;
  query: string;
  marketplaces: string[];
  filters: SearchFilters;
  sort: string;
  status: string;
  error?: string | null;
  createdAt: string;
  completedAt?: string | null;
};

export type Offer = {
  id: string;
  externalId: string;
  marketplace: string;
  title: string;
  price: number;
  oldPrice?: number | null;
  discountPercent?: number | null;
  rating?: number | null;
  reviewsCount?: number | null;
  sellerName?: string | null;
  sellerRating?: number | null;
  imageUrl?: string | null;
  productUrl: string;
  availability: boolean;
  deliveryInfo?: string | null;
  collectedAt: string;
  score: number;
  scoreReasons: string[];
};

export type SearchResults = {
  searchId: string;
  status: string;
  results: Offer[];
};

export type ParserLog = {
  id: string;
  marketplace: string;
  level: string;
  message: string;
  createdAt: string;
};

export type Favorite = {
  id: string;
  offerId?: string | null;
  marketplace: string;
  externalId: string;
  title: string;
  price: number;
  rating?: number | null;
  imageUrl?: string | null;
  productUrl: string;
  score?: number | null;
  createdAt: string;
};

export type TrackedProduct = {
  id: string;
  marketplace: string;
  title: string;
  productUrl: string;
  targetPrice?: number | null;
  lastPrice?: number | null;
  createdAt: string;
};

export type PriceHistoryPoint = {
  id: string;
  trackedProductId: string;
  price: number;
  collectedAt: string;
};

export type Notification = {
  id: string;
  type: string;
  title: string;
  message: string;
  entityId?: string | null;
  isRead: boolean;
  createdAt: string;
};
