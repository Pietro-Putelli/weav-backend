from django.urls.conf import path

from devices.views import logout

urlpatterns = [
    path("logout/", logout, name="logout"),
]
