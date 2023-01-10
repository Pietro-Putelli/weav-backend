from django.contrib import admin

from insights.models import BusinessProfileVisit, BusinessLike, BusinessRepost, BusinessShare, \
    EventRepost, EventShare

BUSINESS_LIST_DISPLAY = ("business", "user", "id")
EVENT_LIST_DISPLAY = ("event", "user", "id")


@admin.register(BusinessProfileVisit)
class BusinessProfileVisitAdmin(admin.ModelAdmin):
    list_display = BUSINESS_LIST_DISPLAY


@admin.register(BusinessLike)
class BusinessLikeAdmin(admin.ModelAdmin):
    list_display = BUSINESS_LIST_DISPLAY


@admin.register(EventRepost)
class EventRepostAdmin(admin.ModelAdmin):
    list_display = EVENT_LIST_DISPLAY


@admin.register(EventShare)
class EventShareAdmin(admin.ModelAdmin):
    list_display = EVENT_LIST_DISPLAY


@admin.register(BusinessRepost)
class BusinessRepostAdmin(admin.ModelAdmin):
    list_display = BUSINESS_LIST_DISPLAY


@admin.register(BusinessShare)
class BusinessShareAdmin(admin.ModelAdmin):
    list_display = BUSINESS_LIST_DISPLAY
