"""Celery app definition.

Phase 0: app boots and registers a no-op task. Phase 1 adds the real
`process_job` task that calls the pipeline orchestrator.

Pre-loads OCR models at worker process startup (Section 1 of optimization plan)
so the first job doesn't pay a cold-start penalty.
"""

from celery import Celery
from celery.signals import worker_process_init

from app.config import get_settings

logger = __import__("logging").getLogger(__name__)


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
        task_routes={
            "converter.process_job": {"queue": "processing"},
            "converter.cleanup_expired_jobs": {"queue": "housekeeping"},
            "converter.publish_scheduled_blog_posts": {"queue": "housekeeping"},
        },
        task_queues={
            "processing": {"exchange": "default", "routing_key": "processing"},
            "housekeeping": {"exchange": "default", "routing_key": "housekeeping"},
        },
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


@worker_process_init.connect
def preload_ocr_models(**kwargs):  # noqa: ANN003
    """Pre-warm PaddleOCR at worker process start.

    Without this hook the first OCR job on each worker process pays a ~3s
    cold-start penalty as PaddleOCR downloads and initialises its models.
    The singleton cache in ``paddle_engine._get_paddle()`` ensures the
    model is loaded exactly once per process regardless of how many times
    this signal fires.
    """
    settings = get_settings()
    if settings.ocr_engine != "paddle":
        logger.info("ocr_engine=%s, skipping PaddleOCR preload", settings.ocr_engine)
        return
    try:
        from app.ocr.paddle_engine import _get_paddle
        lang = settings.ocr_default_paddle_lang or "en"
        logger.info("preloading PaddleOCR model (lang=%s) …", lang)
        _get_paddle(lang)
        logger.info("PaddleOCR model preloaded")
    except Exception as exc:
        logger.warning("PaddleOCR preload failed (will lazy-load on first job): %s", exc)


celery_app = create_celery()
