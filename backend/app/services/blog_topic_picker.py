"""Pick the next blog topic from the content strategy."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.blog_post import BlogPost
from app.models.seo import BlogCategory
from app.services.blog_content_strategy import (
    CALENDAR_BACKLOG,
    COMPARISON_POST_RATIO,
    CONTENT_CALENDAR,
    TOPIC_BACKLOG,
    BlogTopicStrategy,
    infer_category_slug,
    infer_is_comparison,
    slug_from_topic,
)


@dataclass(frozen=True)
class TopicPickResult:
    topic: BlogTopicStrategy
    category_id: str | None
    rationale: str


def _normalize_title(title: str) -> str:
    return title.strip().lower()


def _topic_used(topic: BlogTopicStrategy, used_slugs: set[str], used_titles: set[str]) -> bool:
    slug = slug_from_topic(topic.topic)
    if slug in used_slugs:
        return True
    norm = _normalize_title(topic.topic)
    return norm in used_titles


def _comparison_ratio_recent(posts: list[BlogPost], window: int = 10) -> float:
    recent = [p for p in posts if p.status in ("published", "draft", "scheduled")][:window]
    if not recent:
        return 0.0
    comp_count = sum(1 for p in recent if infer_is_comparison(p.title))
    return comp_count / len(recent)


def _category_counts(posts: list[BlogPost], categories: dict[str, uuid.UUID]) -> dict[str, int]:
    slug_by_id = {v: k for k, v in categories.items()}
    counts = {slug: 0 for slug in categories}
    for post in posts:
        if post.category_id and post.category_id in slug_by_id:
            counts[slug_by_id[post.category_id]] += 1
        else:
            inferred = infer_category_slug(post.title)
            counts[inferred] = counts.get(inferred, 0) + 1
    return counts


def _ordered_candidates() -> list[BlogTopicStrategy]:
    """Calendar first, then weeks 9–16, then extended backlog."""
    seen: set[str] = set()
    out: list[BlogTopicStrategy] = []
    for source in (CONTENT_CALENDAR, CALENDAR_BACKLOG, TOPIC_BACKLOG):
        for t in source:
            key = _normalize_title(t.topic)
            if key in seen:
                continue
            seen.add(key)
            out.append(t)
    return out


def pick_next_topic(db: Session) -> TopicPickResult:
    posts = list(db.scalars(select(BlogPost).order_by(BlogPost.updated_at.desc())).all())
    used_slugs = {p.slug for p in posts}
    used_titles = {_normalize_title(p.title) for p in posts}

    categories = {
        row.slug: row.id
        for row in db.scalars(select(BlogCategory)).all()
    }

    candidates = [
        t for t in _ordered_candidates()
        if not _topic_used(t, used_slugs, used_titles)
    ]
    if not candidates:
        raise ValueError("No unused topics remain in the content strategy")

    current_ratio = _comparison_ratio_recent(posts)
    need_comparison = current_ratio < COMPARISON_POST_RATIO

    cat_counts = _category_counts(posts, categories) if categories else {}
    min_cat_count = min(cat_counts.values()) if cat_counts else 0

    def score(t: BlogTopicStrategy) -> tuple:
        # Prefer calendar order (lower week = higher priority)
        week = t.week if t.week is not None else 999
        cat_count = cat_counts.get(t.category_slug, 0)
        cat_penalty = cat_count - min_cat_count
        comp_match = 0 if t.is_comparison == need_comparison else 1
        return (comp_match, cat_penalty, week)

    candidates.sort(key=score)
    chosen = candidates[0]

    cat_id = categories.get(chosen.category_slug)
    cat_id_str = str(cat_id) if cat_id else None

    rationale_parts = [
        f"comparison_ratio={current_ratio:.0%} (target {COMPARISON_POST_RATIO:.0%})",
        f"prefer_comparison={need_comparison}",
        f"category={chosen.category_slug}",
    ]
    if chosen.week:
        rationale_parts.append(f"calendar_week={chosen.week}")

    return TopicPickResult(
        topic=chosen,
        category_id=cat_id_str,
        rationale="; ".join(rationale_parts),
    )


def resolve_topic(
  topic_str: str,
  *,
  category_slug: str | None = None,
  is_comparison: bool | None = None,
) -> BlogTopicStrategy:
    """Build a BlogTopicStrategy from a custom topic string."""
    cat = category_slug if category_slug else infer_category_slug(topic_str)
    if cat not in ("tutorial", "guide", "workflow", "features"):
        cat = infer_category_slug(topic_str)
    comp = infer_is_comparison(topic_str) if is_comparison is None else is_comparison
    return BlogTopicStrategy(
        topic=topic_str,
        primary_keyword=topic_str.lower()[:80],
        category_slug=cat,  # type: ignore[arg-type]
        comparison_targets=(),
        is_comparison=comp,
    )
