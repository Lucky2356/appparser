import csv
from io import StringIO

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from redis import Redis
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.dependencies import get_current_user
from app.models import Offer, ParserLog, Search, User
from app.searches.schemas import (
    OfferRead,
    ParserLogRead,
    SearchCreate,
    SearchCreated,
    SearchRead,
    SearchResults,
)
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


@router.get("/search/{search_id}/logs", response_model=list[ParserLogRead])
def get_search_logs(
    search_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ParserLog]:
    search = db.get(Search, search_id)
    if not search or search.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search not found")

    return (
        db.query(ParserLog)
        .filter(ParserLog.search_id == search.id)
        .order_by(ParserLog.created_at.asc())
        .all()
    )


@router.get("/search/{search_id}/results.csv")
def export_search_results_csv(
    search_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    search = db.get(Search, search_id)
    if not search or search.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search not found")

    offers = (
        db.query(Offer)
        .filter(Offer.search_id == search.id)
        .order_by(Offer.score.desc(), Offer.price.asc())
        .all()
    )
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["marketplace", "title", "price", "rating", "reviews_count", "score", "product_url"])
    for offer in offers:
        writer.writerow(
            [
                offer.marketplace,
                offer.title,
                offer.price,
                offer.rating,
                offer.reviews_count,
                offer.score,
                offer.product_url,
            ]
        )

    return Response(
        content=buffer.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="search-{search.id}.csv"'},
    )
