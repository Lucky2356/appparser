from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.routes import router as auth_router
from app import models  # noqa: F401
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.favorites.routes import router as favorites_router
from app.images.routes import router as images_router
from app.marketplaces.routes import router as marketplaces_router
from app.notifications.routes import router as notifications_router
from app.searches.routes import router as searches_router
from app.tracked_products.routes import router as tracked_products_router
from app.user_settings.routes import router as user_settings_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.auto_create_tables:
        Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(auth_router)
    app.include_router(images_router)
    app.include_router(marketplaces_router)
    app.include_router(notifications_router)
    app.include_router(searches_router)
    app.include_router(favorites_router)
    app.include_router(tracked_products_router)
    app.include_router(user_settings_router)
    return app


app = create_app()
