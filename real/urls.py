from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from django.urls.conf import include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("users/", include("users.urls")),
    path("profiles/", include("profiles.urls")),
    path("chat/", include("chat.urls")),
    path("business/", include("business.urls")),
    path("moments/", include("moments.urls")),
    path("posts/", include("posts.urls")),
    path("insights/", include("insights.urls")),
    path("discussions/", include("discussions.urls")),
    path("chance/", include("chances.urls")),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
