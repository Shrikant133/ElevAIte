from celery import Celery
import os

# Celery configuration
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

app = Celery(
    "student_crm_worker",
    broker=redis_url,
    backend=redis_url,
    include=[
        "app.tasks.scraping",
        "app.tasks.document_processing", 
        "app.tasks.search_indexing",
        "app.tasks.recommendations",
        "app.tasks.notifications",
        "app.tasks.rules_processor"
    ]
)

# Configuration
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    result_expires=3600,
    task_routes={
        "app.tasks.scraping.*": {"queue": "scraping"},
        "app.tasks.document_processing.*": {"queue": "documents"},
        "app.tasks.search_indexing.*": {"queue": "search"},
        "app.tasks.recommendations.*": {"queue": "recommendations"},
        "app.tasks.notifications.*": {"queue": "notifications"},
        "app.tasks.rules_processor.*": {"queue": "rules"},
    },
    beat_schedule={
        # Daily recommendations
        "generate-daily-recommendations": {
            "task": "app.tasks.recommendations.generate_daily_recommendations",
            "schedule": 3600.0,  # Every hour
        },
        # Rules processing
        "process-rules": {
            "task": "app.tasks.rules_processor.process_all_rules",
            "schedule": 3600.0,  # Every hour  
        },
        # Backup
        "daily-backup": {
            "task": "app.tasks.backup.create_backup",
            "schedule": 86400.0,  # Daily
        }
    }
)

if __name__ == "__main__":
    app.start()