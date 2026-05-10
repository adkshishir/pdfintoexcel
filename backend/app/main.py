"""FastAPI entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin_auth, admin_blog, admin_seo, analytics, blog, health, jobs, landing
from app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    # Hide interactive docs and OpenAPI JSON in production (reduce attack surface).
    expose_docs = settings.env != "prod"
    app = FastAPI(
        title="PDF → Excel Converter",
        version="0.0.1",
        docs_url="/api/docs" if expose_docs else None,
        openapi_url="/api/openapi.json" if expose_docs else None,
        openapi_tags=[
            {
                "name": "admin-auth",
                "description": "Dashboard JWT login, token refresh, and session.",
            },
            {
                "name": "admin-blog",
                "description": "Authenticated CMS for blog posts.",
            },
            {
                "name": "blog",
                "description": "Public blog content (published posts only).",
            },
        ],
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router, prefix="/api")
    app.include_router(admin_auth.router, prefix="/api")
    app.include_router(analytics.router, prefix="/api")
    app.include_router(blog.router, prefix="/api")
    app.include_router(landing.router, prefix="/api")
    app.include_router(admin_blog.router, prefix="/api")
    app.include_router(admin_seo.router, prefix="/api")
    app.include_router(jobs.router, prefix="/api")
    return app


app = create_app()
