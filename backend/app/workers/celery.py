"""
Celery worker configuration for Climate Risk Lens.
"""

from celery import Celery
from celery.schedules import crontab
from app.config import settings

# Create Celery app
celery_app = Celery(
    "climate_risk",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    # Data ingestion tasks
    "fetch-weather-data": {
        "task": "app.workers.tasks.fetch_weather_data",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes
    },
    "fetch-air-quality-data": {
        "task": "app.workers.tasks.fetch_air_quality_data",
        "schedule": crontab(minute="*/10"),  # Every 10 minutes
    },
    "fetch-hydrology-data": {
        "task": "app.workers.tasks.fetch_hydrology_data",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes
    },
    "fetch-fire-data": {
        "task": "app.workers.tasks.fetch_fire_data",
        "schedule": crontab(minute="*/30"),  # Every 30 minutes
    },
    
    # Model inference tasks
    "run-flood-inference": {
        "task": "app.workers.tasks.run_flood_inference",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes
    },
    "run-heat-inference": {
        "task": "app.workers.tasks.run_heat_inference",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes
    },
    "run-smoke-inference": {
        "task": "app.workers.tasks.run_smoke_inference",
        "schedule": crontab(minute="*/10"),  # Every 10 minutes
    },
    
    # Tile generation
    "generate-tiles": {
        "task": "app.workers.tasks.generate_tiles",
        "schedule": crontab(minute="*/30"),  # Every 30 minutes
    },
    
    # Alert processing
    "process-alerts": {
        "task": "app.workers.tasks.process_alerts",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes
    },
    
    # Model retraining (daily)
    "retrain-models": {
        "task": "app.workers.tasks.retrain_models",
        "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    
    # Cleanup tasks
    "cleanup-old-data": {
        "task": "app.workers.tasks.cleanup_old_data",
        "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
    },
}

# Task routing
celery_app.conf.task_routes = {
    "app.workers.tasks.fetch_*": {"queue": "data_ingestion"},
    "app.workers.tasks.run_*_inference": {"queue": "inference"},
    "app.workers.tasks.generate_tiles": {"queue": "tiles"},
    "app.workers.tasks.process_alerts": {"queue": "alerts"},
    "app.workers.tasks.retrain_models": {"queue": "training"},
    "app.workers.tasks.cleanup_*": {"queue": "maintenance"},
}

if __name__ == "__main__":
    celery_app.start()
