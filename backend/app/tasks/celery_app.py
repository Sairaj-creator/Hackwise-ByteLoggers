"""
Celery Application Configuration
==================================
Sets up Celery with RabbitMQ broker and Beat schedule for periodic tasks.
"""

import os
from celery import Celery
from celery.schedules import crontab

# Broker and backend configuration
RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost:5672")
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery = Celery(
    "recipe_generator",
    broker=RABBITMQ_URL,
    backend=REDIS_URL,
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Auto-discover tasks in the tasks package
celery.autodiscover_tasks(["app.tasks"])

# ─── Celery Beat Schedule ───
celery.conf.beat_schedule = {
    "daily-expiry-check": {
        "task": "app.tasks.expiry_checker.daily_expiry_check",
        "schedule": crontab(hour=6, minute=0),  # 6:00 AM daily
    },
    "assign-default-expiry": {
        "task": "app.tasks.expiry_checker.assign_default_expiry_dates",
        "schedule": crontab(hour=6, minute=30),  # 6:30 AM daily
    },
    "weekly-waste-report": {
        "task": "app.tasks.expiry_checker.weekly_waste_report",
        "schedule": crontab(hour=9, minute=0, day_of_week=0),  # Sunday 9 AM
    },
}
