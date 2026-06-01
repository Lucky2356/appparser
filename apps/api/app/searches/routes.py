from fastapi import APIRouter, Depends, HTTPException, status
from redis import Redis
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.dependencies import get_current_user
from app.models import Offer, Search, User
from app.searches.schemas import OfferRead, SearchCreate, SearchCreated, SearchRead, SearchResults
from app.searches.service import process_search
from app.workers.tasks import process_search_task


router = APIRouter(tags=["search"])


def enqueue_or_process_search(search_id: str) -> None:
    try:
        redis_client = Redis.from_url(settings.redis_url, socket_connect_timeout=0.25, socket_timeout=0.25)
        redis_client.ping()
        process_search_task.delay(search_id)
    except Exception:
        # Keeps local development usable even when Redis/Celery is not running.
        process_search(search_id)


@router.post("/search", response_model=SearchCreated)
def create_search(
    payload: SearchCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SearchCreated:
    search = Search(
        user_id=user.id,
        query=payload.query.strip(),
        marketplaces=payload.marketplaces,
        filters=payload.filters.model_dump(),
        sort=payload.sort,
        status="processing",
    )
    db.add(search)
    db.commit()
    db.refresh(search)

    enqueue_or_process_search(search.id)

    return SearchCreated(search_id=search.id, status=search.status)


@router.get("/search/history", response_model=list[SearchRead])
def search_history(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Search]:
    return (
        db.query(Search)
        .filter(Search.user_id == user.id)
        .order_by(Search.created_at.desc())
        .limit(50)
        .all()
    )


@router.get("/search/{search_id}", response_model=SearchRead)
def get_search(
    search_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Search:
    search = db.get(Search, search_id)
    if not search or search.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search not found")
    return search


@router.get("/search/{search_id}/results", response_model=SearchResults)
def get_search_results(
    search_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SearchResults:
    search = db.get(Search, search_id)
    if not search or search.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search not found")

    offers = (
        db.query(Offer)
        .filter(Offer.search_id == search.id)
        .order_by(Offer.score.desc(), Offer.price.asc())
        .limit(20)
        .all()
    )
    return SearchResults(
        search_id=search.id,
        status=search.status,
        results=[OfferRead.model_validate(offer) for offer in offers],
    )
