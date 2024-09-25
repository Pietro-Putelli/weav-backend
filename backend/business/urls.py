from business.views import (
    BusinessFeaturesAPIView,
    search_business,
    get_businesses,
    get_business_by_id,
    BusinessLikeAPIView,
    get_ranked_businesses,
    update_business_profile_settings,
    create_business,
    get_my_business_data,
    BusinessAPIView,
    get_businesses_spot,
)
from django.urls.conf import path, re_path

urlpatterns = [
    path("", BusinessAPIView.as_view()),
    path("create/", create_business),
    path("get/", get_businesses),
    path("get/id/", get_business_by_id),
    path("get/mine/", get_my_business_data),
    path("like/", BusinessLikeAPIView.as_view()),
    path("search/", search_business),
    path("ranked/", get_ranked_businesses),
    path("spot/", get_businesses_spot),
    path("settings/", update_business_profile_settings),
    re_path(r"^(?P<endpoint>[\w]+)/$", BusinessFeaturesAPIView.as_view()),
]
