"""Celery app definition.

Phase 0: app boots and registers a no-op task. Phase 1 adds the real
`process_job` task that calls the pipeline orchestrator.
"""

from celery import Celery

from app.config import get_settings


def create_celery() -> Celery:
    settings = get_settings()
    app = Celery(
        "converter",
        broker=settings.redis_url,
        backend=settings.redis_url,
        include=["app.queue.tasks"],
    )
    app.conf.update(
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        worker_prefetch_multiplier=1,
        task_time_limit=settings.job_timeout_seconds + 60,
        task_soft_time_limit=settings.job_timeout_seconds,
        broker_connection_retry_on_startup=True,
        # Beat schedule (Phase 9). Run the cleanup task every 5 minutes; it
        # deletes expired jobs + sweeps stuck-in-processing rows.
        beat_schedule={
            "cleanup-expired-jobs": {
                "task": "converter.cleanup_expired_jobs",
                "schedule": 5 * 60,
            },
            "publish-scheduled-blog-posts": {
                "task": "converter.publish_scheduled_blog_posts",
                "schedule": 60,
            },
        },
        timezone="UTC",
    )
    return app


celery_app = create_celery()
