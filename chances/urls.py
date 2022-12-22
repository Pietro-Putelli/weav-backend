from django.urls.conf import path

from chances.views import ChanceAPIView

urlpatterns = [
    path("", ChanceAPIView.as_view(), name="chance")
]
