"""Blog content strategy, topic picker, and generation tests."""

from __future__ import annotations

import os
from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.seo import BlogCategory
from app.schemas.blog import BlogPostCreate
from app.services import blog_service
from app.services.blog_content_strategy import (
    infer_category_slug,
    infer_is_comparison,
    slug_from_topic,
)
from app.services.blog_generator import quality_check
from app.services.blog_content_strategy import BlogTopicStrategy
from app.services.blog_topic_picker import pick_next_topic, resolve_topic


def test_infer_is_comparison() -> None:
    assert infer_is_comparison("PDFIntoExcel vs Smallpdf")
    assert infer_is_comparison("Best Adobe Acrobat alternative")
    assert not infer_is_comparison("How to convert bank statement PDF")


def test_infer_category_slug() -> None:
    assert infer_category_slug("How to convert PDF step-by-step") == "tutorial"
    assert infer_category_slug("AP invoice workflow for finance teams") == "workflow"
    assert infer_category_slug("OCR accuracy for scanned PDFs") == "features"
    assert infer_category_slug("Choosing the right converter") == "guide"


def test_slug_from_topic() -> None:
    assert slug_from_topic("Hello World!") == "hello-world"
    assert len(slug_from_topic("a" * 200)) <= 160


def test_resolve_topic_overrides() -> None:
    t = resolve_topic("Custom title", category_slug="workflow", is_comparison=True)
    assert t.category_slug == "workflow"
    assert t.is_comparison is True


def test_llm_client_gemini_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    from app import config
    from app.services import llm_client

    config.get_settings.cache_clear()
    monkeypatch.setenv("BLOG_LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    with patch(
        "app.services.llm_client._gemini_complete_json",
        return_value={"title": "Test"},
    ) as mock_gemini:
        out = llm_client.complete_json("system", "user")
    assert out == {"title": "Test"}
    mock_gemini.assert_called_once()


def test_quality_check_warnings() -> None:
    topic = BlogTopicStrategy(
        topic="Bank Statement PDF to Excel",
        primary_keyword="bank statement pdf to excel",
        category_slug="tutorial",
        comparison_targets=(),
        is_comparison=False,
    )
    payload = {
        "title": "Unrelated title",
        "slug": "test-slug",
        "meta_description": "short",
        "body": "No keyword here.\n\n" + "word " * 100,
        "faqs": [{"q": "Q1", "a": "A1"}],
    }
    warnings = quality_check(payload, topic, existing_slugs=set())
    assert any("keyword" in w for w in warnings)
    assert any("meta_description" in w for w in warnings)
    assert any("FAQ" in w for w in warnings)


def test_quality_check_comparison_table() -> None:
    topic = BlogTopicStrategy(
        topic="PDFIntoExcel vs Smallpdf",
        primary_keyword="smallpdf alternative",
        category_slug="guide",
        comparison_targets=("Smallpdf",),
        is_comparison=True,
    )
    payload = {
        "title": "smallpdf alternative guide",
        "slug": "comp-test",
        "meta_description": "x" * 130,
        "body": "smallpdf alternative intro.\n\n## Compare\n\nNo table here.\n\n" + "word " * 400,
        "faqs": [{"q": f"Q{i}", "a": f"A{i}"} for i in range(5)],
    }
    warnings = quality_check(payload, topic, existing_slugs=set())
    assert any("table" in w for w in warnings)


@pytest.fixture()
def admin_blog_client(tmp_path) -> TestClient:
    db_path = tmp_path / "blog_gen.db"
    storage_root = tmp_path / "storage"
    storage_root.mkdir()

    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["STORAGE_BACKEND"] = "local"
    os.environ["STORAGE_LOCAL_ROOT"] = str(storage_root)
    os.environ["JWT_SECRET"] = "test-jwt-secret-min-32-chars-long!!"
    os.environ["ADMIN_BOOTSTRAP_EMAIL"] = "admin@example.com"
    os.environ["ADMIN_BOOTSTRAP_PASSWORD"] = "bootstrap-pass-123"

    from app import config, storage
    from app.models import database

    config.get_settings.cache_clear()
    storage.get_storage.cache_clear()
    database._engine = None
    database._SessionLocal = None

    from app.models.database import Base, get_engine

    import app.models.admin_user  # noqa: F401
    import app.models.blog_post  # noqa: F401
    import app.models.seo  # noqa: F401

    Base.metadata.create_all(get_engine())

    from app.api import limiter as lim

    lim.enabled = False

    from app.main import app as fastapi_app

    return TestClient(fastapi_app)


def _login(client: TestClient) -> str:
    r = client.post(
        "/api/admin/auth/login",
        json={"email": "admin@example.com", "password": "bootstrap-pass-123"},
    )
    assert r.status_code == 200
    return r.json()["access_token"]


def _seed_categories(db: Session) -> dict[str, str]:
    cats = {}
    for slug, name in [
        ("tutorial", "Tutorial"),
        ("guide", "Guide"),
        ("workflow", "Workflow"),
        ("features", "Features"),
    ]:
        row = BlogCategory(name=name, slug=slug)
        db.add(row)
        db.flush()
        cats[slug] = str(row.id)
    db.commit()
    return cats


def test_pick_next_topic_skips_existing(admin_blog_client: TestClient) -> None:
    from app.models.database import session_scope

    with session_scope() as db:
        _seed_categories(db)
        blog_service.create_post(
            db,
            BlogPostCreate(
                slug="bank-statement-pdf-to-excel",
                title="How to Convert a PDF Bank Statement to Excel (Step-by-Step)",
                meta_description="meta",
                body="body",
                status="published",
                tag_ids=[],
            ),
        )

    with session_scope() as db:
        pick = pick_next_topic(db)
    assert "Bank Statement" not in pick.topic.topic or pick.topic.week != 1


def test_next_topic_requires_auth(admin_blog_client: TestClient) -> None:
    r = admin_blog_client.get("/api/admin/blog/next-topic")
    assert r.status_code == 401


def test_categories_requires_auth(admin_blog_client: TestClient) -> None:
    r = admin_blog_client.get("/api/admin/blog/categories")
    assert r.status_code == 401


def test_generate_requires_auth(admin_blog_client: TestClient) -> None:
    r = admin_blog_client.post("/api/admin/blog/generate", json={})
    assert r.status_code == 401


def test_generate_with_mock_llm(admin_blog_client: TestClient) -> None:
    token = _login(admin_blog_client)
    headers = {"Authorization": f"Bearer {token}"}

    from app.models.database import session_scope

    with session_scope() as db:
        _seed_categories(db)

    mock_payload = {
        "title": "Scanned PDF to Excel: Complete OCR Guide",
        "slug": "scanned-pdf-to-excel-ocr-guide-gen",
        "meta_title": "Scanned PDF to Excel OCR Guide",
        "meta_description": "x" * 130,
        "keywords": "scanned pdf to excel, ocr",
        "body": (
            "scanned pdf to excel conversion starts here.\n\n"
            "## Introduction\n\n"
            "Content.\n\n"
            "## Steps\n\n"
            "1. Upload\n\n"
            "## FAQ\n\n"
            "### Q1?\n\nA1\n\n"
            + "word " * 400
        ),
        "faqs": [{"q": f"Question {i}?", "a": f"Answer {i}."} for i in range(5)],
    }

    with patch(
        "app.services.blog_generator.llm_client.complete_json",
        return_value=mock_payload,
    ):
        r = admin_blog_client.post(
            "/api/admin/blog/generate",
            json={"topic": "Scanned PDF to Excel: Complete OCR Guide"},
            headers=headers,
        )

    assert r.status_code == 201, r.text
    body = r.json()
    assert body["post"]["status"] == "draft"
    assert body["post"]["slug"] == "scanned-pdf-to-excel-ocr-guide-gen"
    assert isinstance(body["quality_warnings"], list)

    r2 = admin_blog_client.get("/api/admin/blog/categories", headers=headers)
    assert r2.status_code == 200
    assert len(r2.json()) == 4

    r3 = admin_blog_client.get("/api/admin/blog/next-topic", headers=headers)
    assert r3.status_code == 200
    assert "topic" in r3.json()
