"""FastAPI entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin_blog, analytics, blog, health, jobs
from app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="PDF → Excel Converter",
        version="0.0.1",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router, prefix="/api")
    app.include_router(analytics.router, prefix="/api")
    app.include_router(blog.router, prefix="/api")
    app.include_router(admin_blog.router, prefix="/api")
    app.include_router(jobs.router, prefix="/api")
    return app


app = create_app()
