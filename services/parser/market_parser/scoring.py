from __future__ import annotations

import math

from market_parser.models import MarketplaceOffer


SCORE_WEIGHTS = {
    "price": 0.40,
    "rating": 0.25,
    "reviews": 0.15,
    "discount": 0.10,
    "seller": 0.10,
}


def rank_offers(offers: list[MarketplaceOffer], sort: str = "best_value") -> list[MarketplaceOffer]:
    if not offers:
        return []

    available_prices = [offer.price for offer in offers if offer.availability and offer.price > 0]
    average_price = sum(available_prices) / len(available_prices) if available_prices else 0
    max_reviews = max((offer.reviews_count or 0 for offer in offers), default=0)

    for offer in offers:
        offer.score, offer.score_reasons = _score_offer(offer, average_price, max_reviews)

    if sort == "price_asc":
        return sorted(offers, key=lambda item: (item.price, -item.score))
    if sort == "rating_desc":
        return sorted(offers, key=lambda item: (-(item.rating or 0), -item.score))
    return sorted(offers, key=lambda item: (-item.score, item.price))


def _score_offer(offer: MarketplaceOffer, average_price: float, max_reviews: int) -> tuple[float, list[str]]:
    price_score, price_reason, suspicious_penalty = _price_score(offer.price, average_price)
    rating_score, rating_reason = _rating_score(offer.rating)
    reviews_score, reviews_reason = _reviews_score(offer.reviews_count, max_reviews)
    discount_score, discount_reason = _discount_score(offer.discount_percent)
    seller_score, seller_reason = _seller_score(offer.seller_rating)

    score = (
        price_score * SCORE_WEIGHTS["price"]
        + rating_score * SCORE_WEIGHTS["rating"]
        + reviews_score * SCORE_WEIGHTS["reviews"]
        + discount_score * SCORE_WEIGHTS["discount"]
        + seller_score * SCORE_WEIGHTS["seller"]
    )

    if not offer.availability:
        score *= 0.55
    if suspicious_penalty:
        score *= 0.50

    reasons = [
        reason
        for reason in [
            price_reason,
            rating_reason,
            reviews_reason,
            discount_reason,
            seller_reason,
            "Есть доставка" if offer.availability and offer.delivery_info else "Наличие требует проверки",
        ]
        if reason
    ]
    return round(max(0, min(100, score)), 1), reasons[:5]


def _price_score(price: float, average_price: float) -> tuple[float, str, bool]:
    if not average_price:
        return 50, "", False

    delta = (average_price - price) / average_price
    suspicious = price < average_price * 0.55

    if delta >= 0:
        score = 72 + min(delta * 100, 28)
        reason = f"Цена ниже средней на {round(delta * 100)}%"
    else:
        score = max(12, 72 + delta * 120)
        reason = f"Цена выше средней на {abs(round(delta * 100))}%"

    if suspicious:
        reason = f"{reason}, цена выглядит подозрительно низкой"
    return score, reason, suspicious


def _rating_score(rating: float | None) -> tuple[float, str]:
    if rating is None:
        return 40, "Нет рейтинга товара"
    score = max(0, min(100, (rating / 5) * 100))
    if rating >= 4.8:
        return score, f"Высокий рейтинг {rating}"
    if rating >= 4.5:
        return score, f"Рейтинг {rating}"
    return score * 0.75, f"Рейтинг ниже топовых предложений: {rating}"


def _reviews_score(reviews: int | None, max_reviews: int) -> tuple[float, str]:
    reviews = reviews or 0
    if reviews == 0:
        return 12, "Пока нет отзывов"
    if max_reviews <= 0:
        return 50, f"{reviews} отзывов"

    score = math.log10(reviews + 1) / math.log10(max_reviews + 1) * 100
    if reviews >= 1000:
        return score, f"Более {reviews} отзывов"
    if reviews >= 100:
        return score, f"{reviews} отзывов"
    return score * 0.7, f"Мало отзывов: {reviews}"


def _discount_score(discount: int | None) -> tuple[float, str]:
    if not discount:
        return 35, ""
    score = min(100, discount / 35 * 100)
    return score, f"Скидка {discount}%"


def _seller_score(seller_rating: float | None) -> tuple[float, str]:
    if seller_rating is None:
        return 50, ""
    score = max(0, min(100, (seller_rating / 5) * 100))
    if seller_rating >= 4.7:
        return score, f"Продавец с рейтингом {seller_rating}"
    return score * 0.8, f"Рейтинг продавца {seller_rating}"
