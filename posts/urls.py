from django.urls.conf import path

from posts.views import UserPostAPIView, BusinessPostAPIView, get_business_posts

urlpatterns = [
    path("user/", UserPostAPIView.as_view()),
    path("business/", BusinessPostAPIView.as_view()),
    path("business/get/", get_business_posts)
]
