from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Notification, Offer, PriceHistory, TrackedProduct
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
        maybe_create_price_notification(db, item, None, last_price)

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
    previous_price = item.last_price
    item.last_price = best_match.price
    item.last_checked_at = datetime.now(timezone.utc)
    db.add(PriceHistory(tracked_product_id=item.id, price=best_match.price))
    maybe_create_price_notification(db, item, previous_price, best_match.price)
    db.commit()
    db.refresh(item)
    return item


def maybe_create_price_notification(
    db: Session,
    item: TrackedProduct,
    previous_price: float | None,
    current_price: float,
) -> None:
    target_reached = item.target_price is not None and current_price <= item.target_price
    price_dropped = previous_price is not None and current_price < previous_price

    if not target_reached and not price_dropped:
        return
    if item.last_notified_price is not None and current_price >= item.last_notified_price:
        return

    if target_reached:
        title = "Цена достигла цели"
        message = f"{item.title}: цена снизилась до {current_price:,.0f} ₽"
        notification_type = "target_price_reached"
    else:
        title = "Цена снизилась"
        message = f"{item.title}: было {previous_price:,.0f} ₽, стало {current_price:,.0f} ₽"
        notification_type = "price_drop"

    db.add(
        Notification(
            user_id=item.user_id,
            type=notification_type,
            title=title,
            message=message.replace(",", " "),
            entity_id=item.id,
        )
    )
    item.last_notified_price = current_price


def refresh_all_tracked_products(db: Session) -> int:
    refreshed = 0
    items = db.query(TrackedProduct).order_by(TrackedProduct.created_at.asc()).all()
    for item in items:
        refresh_tracked_product(db, item)
        refreshed += 1
    return refreshed
