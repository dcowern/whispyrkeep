# WhispyrKeep Django Project
# Import Celery app on Django startup

from whispyrkeep.celery import app as celery_app

__all__ = ("celery_app",)
