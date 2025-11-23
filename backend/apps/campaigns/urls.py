from django.urls import path

from apps.campaigns import views

urlpatterns = [
    path("", views.CampaignListCreateView.as_view(), name="campaign_list"),
    path("<uuid:pk>/", views.CampaignDetailView.as_view(), name="campaign_detail"),
    path("<uuid:pk>/turn/", views.TurnView.as_view(), name="campaign_turn"),
    path("<uuid:pk>/turns/", views.TurnListView.as_view(), name="turn_list"),
    path("<uuid:pk>/state/", views.StateView.as_view(), name="campaign_state"),
    path("<uuid:pk>/dice-log/", views.DiceLogView.as_view(), name="dice_log"),
    path("<uuid:pk>/rewind/", views.RewindView.as_view(), name="campaign_rewind"),
    path("<uuid:pk>/export/", views.CampaignExportView.as_view(), name="campaign_export"),
]
