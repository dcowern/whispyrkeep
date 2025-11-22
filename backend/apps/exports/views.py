"""Export views - Placeholder implementations."""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class ExportJobDetailView(APIView):
    """GET /api/exports/{job_id} - Check export status."""

    def get(self, request, job_id):
        return Response(
            {"detail": "Export job status - to be implemented in Epic 11"},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )
