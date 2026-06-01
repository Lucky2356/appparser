from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models import Offer, PriceHistory, Search, TrackedProduct, User
from app.tracked_products.schemas import (
    PriceHistoryRead,
    RefreshAllResponse,
    TrackedProductCreate,
    TrackedProductFromOffer,
    TrackedProductRead,
)
from app.tracked_products.service import (
    create_tracked_product as create_tracked_product_record,
    create_tracked_product_from_offer,
    refresh_tracked_product,
)


router = APIRouter(tags=["tracked-products"])


@router.post("/tracked-products", response_model=TrackedProductRead)
def create_tracked_product(
    payload: TrackedProductCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TrackedProduct:
    return create_tracked_product_record(
        db,
        user_id=user.id,
        marketplace=payload.marketplace,
        title=payload.title,
        product_url=payload.product_url,
        target_price=payload.target_price,
        last_price=payload.last_price,
    )


@router.post("/tracked-products/from-offer", response_model=TrackedProductRead)
def create_tracked_from_offer(
    payload: TrackedProductFromOffer,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TrackedProduct:
    offer = db.query(Offer).join(Search).filter(Offer.id == payload.offer_id, Search.user_id == user.id).first()
    if not offer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")

    return create_tracked_product_from_offer(
        db,
        user_id=user.id,
        offer=offer,
        target_price=payload.target_price,
    )


@router.get("/tracked-products", response_model=list[TrackedProductRead])
def list_tracked_products(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[TrackedProduct]:
    return (
        db.query(TrackedProduct)
        .filter(TrackedProduct.user_id == user.id)
        .order_by(TrackedProduct.created_at.desc())
        .all()
    )


@router.delete("/tracked-products/{tracked_product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tracked_product(
    tracked_product_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    item = (
        db.query(TrackedProduct)
        .filter(TrackedProduct.id == tracked_product_id, TrackedProduct.user_id == user.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tracked product not found")

    db.delete(item)
    db.commit()


@router.get("/tracked-products/{tracked_product_id}/price-history", response_model=list[PriceHistoryRead])
def list_price_history(
    tracked_product_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[PriceHistory]:
    item = (
        db.query(TrackedProduct)
        .filter(TrackedProduct.id == tracked_product_id, TrackedProduct.user_id == user.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tracked product not found")

    return (
        db.query(PriceHistory)
        .filter(PriceHistory.tracked_product_id == item.id)
        .order_by(PriceHistory.collected_at.asc())
        .all()
    )


@router.post("/tracked-products/{tracked_product_id}/refresh", response_model=TrackedProductRead)
def refresh_tracked(
    tracked_product_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TrackedProduct:
    item = (
        db.query(TrackedProduct)
        .filter(TrackedProduct.id == tracked_product_id, TrackedProduct.user_id == user.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tracked product not found")

    return refresh_tracked_product(db, item)


@router.post("/tracked-products/refresh-all", response_model=RefreshAllResponse)
def refresh_all_tracked(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RefreshAllResponse:
    items = db.query(TrackedProduct).filter(TrackedProduct.user_id == user.id).all()
    refreshed = 0
    for item in items:
        refresh_tracked_product(db, item)
        refreshed += 1
    return RefreshAllResponse(refreshed=refreshed)
