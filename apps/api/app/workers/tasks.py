from app.db.session import SessionLocal
from app.models import TrackedProduct
from app.searches.service import process_search
from app.tracked_products.service import refresh_all_tracked_products, refresh_tracked_product
from app.workers.celery_app import celery_app


@celery_app.task(name="app.process_search")
def process_search_task(search_id: str) -> None:
    process_search(search_id)


@celery_app.task(name="app.refresh_tracked_product")
def refresh_tracked_product_task(tracked_product_id: str) -> None:
    db = SessionLocal()
    try:
        item = db.get(TrackedProduct, tracked_product_id)
        if item:
            refresh_tracked_product(db, item)
    finally:
        db.close()


@celery_app.task(name="app.refresh_all_tracked_products")
def refresh_all_tracked_products_task() -> int:
    db = SessionLocal()
    try:
        return refresh_all_tracked_products(db)
    finally:
        db.close()
