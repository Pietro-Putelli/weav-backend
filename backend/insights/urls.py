from django.urls.conf import path

from insights.views import EventMomentInsightsAPIView, get_insights_detail, \
    get_insights_overview

urlpatterns = [
    path("event/", EventMomentInsightsAPIView.as_view(), name="event_moment_insights"),
    path("overview/", get_insights_overview, name="insights_overview"),
    path("detail/", get_insights_detail, name="insights_detail")
]
