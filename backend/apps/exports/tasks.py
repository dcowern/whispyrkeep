"""
Celery tasks for export operations.

Based on SYSTEM_DESIGN.md section 14:
- render_export(job_id, format)
- Uses export_queue
"""

import logging

from celery import shared_task

from apps.exports.models import ExportJob
from apps.exports.services.export_service import ExportService

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    queue="export_queue",
    max_retries=2,
    default_retry_delay=30,
)
def render_export(self, job_id: str) -> dict:
    """
    Execute an export job asynchronously.

    Args:
        job_id: UUID of the export job to execute

    Returns:
        Dict with status and result info
    """
    try:
        job = ExportJob.objects.get(id=job_id)
    except ExportJob.DoesNotExist:
        logger.error(f"Export job {job_id} not found")
        return {"success": False, "error": "Job not found"}

    if job.status not in ["pending", "processing"]:
        logger.info(f"Export job {job_id} already in status: {job.status}")
        return {"success": False, "error": f"Job already {job.status}"}

    service = ExportService()
    result = service.execute_export(job)

    if result.success:
        logger.info(f"Export job {job_id} completed successfully")
        return {
            "success": True,
            "job_id": str(job_id),
            "filename": result.filename,
            "content_type": result.content_type,
        }
    else:
        logger.error(f"Export job {job_id} failed: {result.errors}")
        return {
            "success": False,
            "job_id": str(job_id),
            "errors": result.errors,
        }
