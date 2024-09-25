from django.contrib import admin

from business.models import (
    Business,
    BusinessToken,
    BusinessTimetable,
    BusinessHighlight,
)


@admin.register(Business)
class NotApprovedBusiness(admin.ModelAdmin):
    list_display = ("name", "id", "category", "is_approved", "created_at")
    list_filter = ("is_approved",)

    @admin.action(description="Mark selected business as approved")
    def approve_business(_, __, queryset):
        for business in queryset:
            business.is_approved = True
            business.save()

    actions = [approve_business]


@admin.register(BusinessToken)
class BusinessTokenAdmin(admin.ModelAdmin):
    list_display = ("business", "key")


class BusinessNameAdminModel(admin.ModelAdmin):
    def get_business(self, obj):
        if obj.business is not None:
            return obj.business.name
        return None


@admin.register(BusinessTimetable)
class BusinessTimetableAdmin(BusinessNameAdminModel):
    list_display = ("business", "id")


@admin.register(BusinessHighlight)
class BusinessHighlightAdmin(BusinessNameAdminModel):
    list_display = ("business", "id")
