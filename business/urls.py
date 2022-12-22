from django.urls.conf import path, re_path

from business.views import BusinessFeaturesAPIView, \
    search_business, get_businesses, get_business_by_id, BusinessLikeAPIView, get_ranked_businesses, \
    get_my_businesses, get_business_current_moment, test_business_auth, \
    update_business_profile_settings, create_business, get_my_business_data, \
    BusinessAPIView

urlpatterns = [
    path("", BusinessAPIView.as_view()),
    path("create/", create_business),

    path("get/", get_businesses),
    path("get/id/", get_business_by_id),

    path("get/list/", get_my_businesses),
    path("get/mine/", get_my_business_data),

    path("like/", BusinessLikeAPIView.as_view()),
    path("search/", search_business),
    path("ranked/", get_ranked_businesses),
    path("moment/", get_business_current_moment),

    path("settings/", update_business_profile_settings),

    path("test/", test_business_auth),
    re_path(r"^(?P<endpoint>[\w]+)/$", BusinessFeaturesAPIView.as_view())
]
