"""
Export views - Export job management and status checking.

Based on SYSTEM_DESIGN.md section 13.7:
- GET /api/exports/{job_id} - Check export status
- GET /api/exports/ - List user's export jobs
"""

from django.http import HttpResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.exports.models import ExportJob
from apps.exports.serializers import (
    ExportJobListSerializer,
    ExportJobSerializer,
)
from apps.exports.services.export_service import ExportService


class ExportJobListView(APIView):
    """GET /api/exports/ - List user's export jobs."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List user's export jobs."""
        jobs = ExportJob.objects.filter(user=request.user).order_by("-created_at")

        # Apply filters
        export_type = request.query_params.get("type")
        if export_type:
            jobs = jobs.filter(export_type=export_type)

        status_filter = request.query_params.get("status")
        if status_filter:
            jobs = jobs.filter(status=status_filter)

        # Pagination
        limit = int(request.query_params.get("limit", 20))
        offset = int(request.query_params.get("offset", 0))
        jobs = jobs[offset:offset + limit]

        serializer = ExportJobListSerializer(jobs, many=True)
        return Response({
            "count": ExportJob.objects.filter(user=request.user).count(),
            "results": serializer.data,
        })


class ExportJobDetailView(APIView):
    """GET /api/exports/{job_id} - Check export status and download."""

    permission_classes = [IsAuthenticated]

    def get(self, request, job_id):
        """Get export job status or download content."""
        try:
            job = ExportJob.objects.get(id=job_id, user=request.user)
        except ExportJob.DoesNotExist:
            return Response(
                {"error": "Export job not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if user wants to download
        download = request.query_params.get("download", "").lower() == "true"

        if download and job.status == "completed":
            # Re-execute export to get content for download
            # In production, this would fetch from file storage
            service = ExportService()
            result = service.execute_export(job)

            if result.success:
                response = HttpResponse(
                    result.content,
                    content_type=result.content_type,
                )
                response["Content-Disposition"] = f'attachment; filename="{result.filename}"'
                return response
            else:
                return Response(
                    {"error": "Failed to generate export", "details": result.errors},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        serializer = ExportJobSerializer(job)
        return Response(serializer.data)

    def delete(self, request, job_id):
        """Cancel/delete an export job."""
        try:
            job = ExportJob.objects.get(id=job_id, user=request.user)
        except ExportJob.DoesNotExist:
            return Response(
                {"error": "Export job not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if job.status == "processing":
            return Response(
                {"error": "Cannot delete a job that is currently processing"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        job.delete()
        return Response(
            {"message": "Export job deleted"},
            status=status.HTTP_200_OK,
        )
