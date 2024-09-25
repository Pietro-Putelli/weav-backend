from django.conf import settings
from django.contrib import admin
from django.urls import path
from django.urls.conf import include

urlpatterns = [
    path("users/", include("users.urls")),
    path("profiles/", include("profiles.urls")),
    path("chat/", include("chat.urls")),
    path("business/", include("business.urls")),
    path("moments/", include("moments.urls")),
    path("posts/", include("posts.urls")),
    path("insights/", include("insights.urls")),
    path("discussions/", include("discussions.urls")),
    path("devices/", include("devices.urls")),
    path("spots/", include("spots.urls")),
]

admin_url = "fdf1b418ddcf29c250db1ea840ce0978"

if settings.DEBUG:
    admin_url = "admin"

urlpatterns += [path(f"{admin_url}/", admin.site.urls)]
