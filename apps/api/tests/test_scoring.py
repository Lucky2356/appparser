from market_parser.models import MarketplaceOffer
from market_parser.scoring import rank_offers


def test_scoring_prefers_balanced_value_over_suspicious_low_price():
    offers = [
        MarketplaceOffer(
            external_id="cheap",
            marketplace="ozon",
            title="Too cheap",
            price=10_000,
            product_url="https://example.com/cheap",
            rating=4.1,
            reviews_count=4,
            seller_rating=3.8,
            discount_percent=40,
        ),
        MarketplaceOffer(
            external_id="balanced",
            marketplace="wildberries",
            title="Balanced",
            price=42_000,
            product_url="https://example.com/balanced",
            rating=4.8,
            reviews_count=1800,
            seller_rating=4.8,
            discount_percent=14,
        ),
    ]

    ranked = rank_offers(offers)
    assert ranked[0].external_id == "balanced"
    assert ranked[0].score_reasons
