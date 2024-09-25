from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND

from authentication.decorators import business_authentication
from authentication.api_views import BusinessAuthenticationAPIView
from insights.serializers import (
    OverviewInsightsSerializer,
    LikeInsightsSerializer,
    SummaryInsightsSerializer,
    RepostAndShareInsightsSerializer,
    EventMomentInsightSerializer,
)
from insights.utils import (
    INSIGHT_TYPES,
    create_profile_visit_insight,
    create_likes_insight,
    create_insights_overview,
    create_summary_insights,
    create_reposts_insight,
    create_shares_insight,
)
from moments.models import EventMoment


class EventMomentInsightsAPIView(BusinessAuthenticationAPIView):
    def get(self, request):
        params = request.query_params
        event_id = params.get("eventId")

        try:
            event = EventMoment.objects.get(uuid=event_id)
        except EventMoment.DoesNotExist:
            return Response(status=HTTP_404_NOT_FOUND)

        insights = EventMomentInsightSerializer(event)

        return Response(insights.data, status=HTTP_200_OK)


@api_view(["GET"])
@business_authentication
def get_insights_detail(request):
    params = request.query_params

    type = params.get("type")
    to_date = params.get("to")
    from_date = params.get("from")
    business = request.business

    shared_params = (business, from_date, to_date)

    if type == INSIGHT_TYPES.reposts:
        insight = create_reposts_insight(*shared_params)
        insight = RepostAndShareInsightsSerializer(insight).data
    elif type == INSIGHT_TYPES.shares:
        insight = create_shares_insight(*shared_params)
        insight = RepostAndShareInsightsSerializer(insight).data
    elif type == INSIGHT_TYPES.visits:
        insight = create_profile_visit_insight(*shared_params)
    elif type == INSIGHT_TYPES.likes:
        insight = create_likes_insight(*shared_params)
        insight = LikeInsightsSerializer(insight).data
    elif type == INSIGHT_TYPES.summary:
        insight = create_summary_insights(*shared_params)
        insight = SummaryInsightsSerializer(insight).data
    else:
        insight = None

    return Response(insight, status=HTTP_200_OK)


@api_view(["GET"])
@business_authentication
def get_insights_overview(request):
    params = request.query_params

    overview = create_insights_overview(request.business, params)
    overview = OverviewInsightsSerializer(overview)

    return Response(overview.data, status=HTTP_200_OK)
