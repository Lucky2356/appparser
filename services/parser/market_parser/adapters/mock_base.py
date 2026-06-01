from __future__ import annotations

import hashlib
import random
from urllib.parse import quote_plus
from uuid import NAMESPACE_URL, uuid5

from market_parser.adapters.base import MarketplaceAdapter
from market_parser.models import MarketplaceOffer, SearchFilters, SearchParams


class BaseMockMarketplaceAdapter(MarketplaceAdapter):
    display_name: str
    brand_color: str
    price_multiplier: float = 1.0

    def search_products(self, params: SearchParams) -> list[MarketplaceOffer]:
        query = params.query.strip()
        rng = random.Random(self._seed(query))
        base_price = self._base_price(query)
        offers: list[MarketplaceOffer] = []

        for index, profile in enumerate(self._profiles()):
            price_factor, rating, reviews, discount, seller, seller_rating, delivery = profile
            noise = rng.uniform(-0.055, 0.065)
            price = round(base_price * self.price_multiplier * price_factor * (1 + noise), -1)
            old_price = round(price / (1 - discount / 100), -1) if discount else None
            external_id = self._external_id(query, index)
            title = self._title(query, index)

            offers.append(
                MarketplaceOffer(
                    external_id=external_id,
                    marketplace=self.marketplace_name,
                    title=title,
                    price=float(max(price, 250)),
                    old_price=float(old_price) if old_price else None,
                    discount_percent=discount,
                    rating=round(min(5, max(3.7, rating + rng.uniform(-0.08, 0.06))), 1),
                    reviews_count=max(0, int(reviews * rng.uniform(0.82, 1.24))),
                    seller_name=seller,
                    seller_rating=round(min(5, max(3.5, seller_rating + rng.uniform(-0.05, 0.05))), 1),
                    image_url=self._image_url(title),
                    product_url=self._product_url(external_id, query),
                    availability=index % 9 != 8,
                    delivery_info=delivery,
                )
            )

        return self._apply_filters(offers, params.filters)

    def _seed(self, query: str) -> int:
        digest = hashlib.sha256(f"{self.marketplace_name}:{query.lower()}".encode("utf-8")).hexdigest()
        return int(digest[:12], 16)

    def _external_id(self, query: str, index: int) -> str:
        return f"{self.marketplace_name}-{uuid5(NAMESPACE_URL, f'{self.marketplace_name}:{query}:{index}').hex[:12]}"

    def _base_price(self, query: str) -> float:
        normalized = query.lower()
        if any(word in normalized for word in ["телефон", "phone", "iphone", "samsung", "xiaomi"]):
            return 52000
        if any(word in normalized for word in ["ноутбук", "laptop", "macbook"]):
            return 82000
        if any(word in normalized for word in ["наушники", "headphones", "airpods"]):
            return 12000
        if any(word in normalized for word in ["кроссовки", "обувь", "sneakers"]):
            return 7200
        return 18000

    def _profiles(self) -> list[tuple[float, float, int, int, str, float, str]]:
        return [
            (0.78, 4.8, 1850, 18, "Market Pro", 4.8, "Доставка завтра"),
            (0.84, 4.7, 930, 12, "TechPoint", 4.7, "Пункт выдачи 1-2 дня"),
            (0.91, 4.9, 4100, 8, "Official Store", 4.9, "Есть экспресс-доставка"),
            (0.69, 4.4, 85, 25, "Sale Outlet", 4.2, "Доставка 3-5 дней"),
            (1.03, 4.8, 2700, 5, "Gadget Line", 4.8, "Доставка завтра"),
            (0.74, 4.6, 540, 21, "Best Choice", 4.6, "Пункт выдачи завтра"),
            (1.12, 4.9, 6200, 0, "Premium Seller", 5.0, "Курьер 1-2 дня"),
            (0.57, 4.1, 14, 34, "New Seller", 3.9, "Доставка 5-7 дней"),
            (0.88, 4.7, 1500, 16, "City Market", 4.7, "Есть доставка"),
            (0.96, 4.5, 310, 10, "Discount Zone", 4.4, "Пункт выдачи 2 дня"),
            (0.81, 4.9, 980, 19, "Fast Retail", 4.8, "Доставка завтра"),
            (1.18, 5.0, 720, 4, "Brand Partner", 4.9, "Официальная гарантия"),
        ]

    def _title(self, query: str, index: int) -> str:
        suffixes = [
            "оптимальная версия",
            "с гарантией магазина",
            "популярный комплект",
            "базовая комплектация",
            "расширенная версия",
            "выгодный набор",
            "официальная поставка",
            "новый продавец",
            "хит продаж",
            "эконом-предложение",
            "быстрая доставка",
            "премиальная версия",
        ]
        return f"{query.strip().title()} - {suffixes[index % len(suffixes)]}"

    def _image_url(self, title: str) -> str:
        text = quote_plus(self.display_name)
        return f"https://placehold.co/640x420/{self.brand_color}/0f172a?text={text}"

    def _product_url(self, external_id: str, query: str) -> str:
        encoded_query = quote_plus(query)
        return f"https://example.com/{self.marketplace_name}/product/{external_id}?q={encoded_query}"

    def _apply_filters(self, offers: list[MarketplaceOffer], filters: SearchFilters) -> list[MarketplaceOffer]:
        result = offers
        if filters.min_rating is not None:
            result = [offer for offer in result if (offer.rating or 0) >= filters.min_rating]
        if filters.min_reviews is not None:
            result = [offer for offer in result if (offer.reviews_count or 0) >= filters.min_reviews]
        if filters.min_price is not None:
            result = [offer for offer in result if offer.price >= filters.min_price]
        if filters.max_price is not None:
            result = [offer for offer in result if offer.price <= filters.max_price]
        return result
