from sqlalchemy.orm import Session

from app.models import Offer, PriceHistory, TrackedProduct
from market_parser.models import SearchFilters, SearchParams
from market_parser.scoring import rank_offers
from market_parser.service import collect_offers


def create_tracked_product(
    db: Session,
    *,
    user_id: str,
    marketplace: str,
    title: str,
    product_url: str,
    target_price: float | None,
    last_price: float | None,
) -> TrackedProduct:
    item = TrackedProduct(
        user_id=user_id,
        marketplace=marketplace,
        title=title,
        product_url=product_url,
        target_price=target_price,
        last_price=last_price,
    )
    db.add(item)
    db.flush()

    if last_price is not None:
        db.add(PriceHistory(tracked_product_id=item.id, price=last_price))

    db.commit()
    db.refresh(item)
    return item


def create_tracked_product_from_offer(
    db: Session,
    *,
    user_id: str,
    offer: Offer,
    target_price: float | None,
) -> TrackedProduct:
    return create_tracked_product(
        db,
        user_id=user_id,
        marketplace=offer.marketplace,
        title=offer.title,
        product_url=offer.product_url,
        target_price=target_price,
        last_price=offer.price,
    )


def refresh_tracked_product(db: Session, item: TrackedProduct) -> TrackedProduct:
    params = SearchParams(
        query=item.title,
        marketplaces=[item.marketplace],
        filters=SearchFilters(),
        sort="best_value",
    )
    collected = collect_offers(params)
    ranked = rank_offers(collected.offers)
    if not ranked:
        return item

    best_match = ranked[0]
    item.last_price = best_match.price
    db.add(PriceHistory(tracked_product_id=item.id, price=best_match.price))
    db.commit()
    db.refresh(item)
    return item
