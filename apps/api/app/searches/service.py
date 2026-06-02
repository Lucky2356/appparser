import os
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import Offer, ParserLog, Search
from market_parser.models import SearchFilters as ParserFilters
from market_parser.models import SearchParams
from market_parser.scoring import rank_offers
from market_parser.service import collect_offers


def _parser_filters(raw: dict[str, Any] | None) -> ParserFilters:
    raw = raw or {}
    return ParserFilters(
        min_rating=raw.get("min_rating") or raw.get("minRating"),
        min_reviews=raw.get("min_reviews") or raw.get("minReviews"),
        min_price=raw.get("min_price") or raw.get("minPrice"),
        max_price=raw.get("max_price") or raw.get("maxPrice"),
    )


def process_search(search_id: str) -> None:
    db = SessionLocal()
    try:
        _process_search_with_session(db, search_id)
    finally:
        db.close()


def _process_search_with_session(db: Session, search_id: str) -> None:
    search = db.get(Search, search_id)
    if not search:
        return

    search.status = "processing"
    search.error = None
    db.commit()

    try:
        params = SearchParams(
            query=search.query,
            marketplaces=search.marketplaces,
            filters=_parser_filters(search.filters),
            sort=search.sort,
        )

        collected = collect_offers(params)
        ranked = rank_offers(collected.offers, sort=search.sort)

        db.query(Offer).filter(Offer.search_id == search.id).delete()
        db.query(ParserLog).filter(ParserLog.search_id == search.id).delete()

        for log in collected.logs:
            db.add(
                ParserLog(
                    search_id=search.id,
                    marketplace=log.marketplace,
                    level=log.level,
                    message=log.message,
                )
            )

        if _should_fail_real_search(collected.offers, collected.logs):
            raise RuntimeError("Live marketplace sources did not return real offers. Check parser logs for source errors.")

        for item in ranked[:50]:
            db.add(
                Offer(
                    search_id=search.id,
                    external_id=item.external_id,
                    marketplace=item.marketplace,
                    title=item.title,
                    price=item.price,
                    old_price=item.old_price,
                    discount_percent=item.discount_percent,
                    rating=item.rating,
                    reviews_count=item.reviews_count,
                    seller_name=item.seller_name,
                    seller_rating=item.seller_rating,
                    image_url=item.image_url,
                    product_url=item.product_url,
                    availability=item.availability,
                    delivery_info=item.delivery_info,
                    collected_at=item.collected_at,
                    score=item.score,
                    score_reasons=item.score_reasons,
                )
            )

        search.status = "completed"
        search.completed_at = datetime.now(timezone.utc)
        db.commit()
    except Exception as exc:  # noqa: BLE001
        search.status = "failed"
        search.error = str(exc)
        search.completed_at = datetime.now(timezone.utc)
        db.add(
            ParserLog(
                search_id=search.id,
                marketplace="system",
                level="error",
                message=str(exc),
            )
        )
        db.commit()


def _should_fail_real_search(offers: list, logs: list) -> bool:
    if os.getenv("PARSER_MODE", "mock").lower() != "real" or offers:
        return False
    source_failures = [
        log
        for log in logs
        if log.level == "error" or log.message.startswith("Adapter source: failed")
    ]
    return bool(source_failures)
