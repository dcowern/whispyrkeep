from django.urls import path

from apps.exports import views

urlpatterns = [
    path("", views.ExportJobListView.as_view(), name="export_job_list"),
    path("<uuid:job_id>/", views.ExportJobDetailView.as_view(), name="export_job_detail"),
]
