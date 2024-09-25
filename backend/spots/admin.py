from django.contrib import admin
from spots.models import Spot
from django.utils import timezone

@admin.register(Spot)
class SpotAdmin(admin.ModelAdmin):
    list_display = ("business", "profile", "id")

    @admin.action(description="Delete expired spots")
    def delete_expired_spots(_, __, queryset):
        for spot in queryset:
            # check if created_at is two days ago
            if spot.created_at < timezone.now() - timedelta(days=2):
                spot.delete()

    actions = [delete_expired_spots]

