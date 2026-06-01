from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_user
from app.favorites.schemas import FavoriteCreate, FavoriteRead
from app.models import Favorite, Offer, Search, User


router = APIRouter(tags=["favorites"])


@router.post("/favorites", response_model=FavoriteRead)
def add_favorite(
    payload: FavoriteCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Favorite:
    offer = db.query(Offer).join(Search).filter(Offer.id == payload.offer_id, Search.user_id == user.id).first()
    if not offer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")

    existing = (
        db.query(Favorite)
        .filter(Favorite.user_id == user.id, Favorite.offer_id == offer.id)
        .first()
    )
    if existing:
        return existing

    favorite = Favorite(
        user_id=user.id,
        offer_id=offer.id,
        marketplace=offer.marketplace,
        external_id=offer.external_id,
        title=offer.title,
        price=offer.price,
        rating=offer.rating,
        image_url=offer.image_url,
        product_url=offer.product_url,
        score=offer.score,
    )
    db.add(favorite)
    db.commit()
    db.refresh(favorite)
    return favorite


@router.get("/favorites", response_model=list[FavoriteRead])
def list_favorites(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Favorite]:
    return (
        db.query(Favorite)
        .filter(Favorite.user_id == user.id)
        .order_by(Favorite.created_at.desc())
        .all()
    )


@router.delete("/favorites/{favorite_or_offer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_favorite(
    favorite_or_offer_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    favorite = (
        db.query(Favorite)
        .filter(
            Favorite.user_id == user.id,
            or_(Favorite.id == favorite_or_offer_id, Favorite.offer_id == favorite_or_offer_id),
        )
        .first()
    )
    if not favorite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Favorite not found")

    db.delete(favorite)
    db.commit()
