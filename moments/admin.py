from django.contrib import admin
from django.utils.text import Truncator

from moments.models import EventMoment, EventMomentSlice, UserMoment


class MomentAdmin(admin.ModelAdmin):
    list_display = ('id', 'text_content', 'has_source', 'has_business', 'has_url', 'has_location')
    readonly_fields = ('uuid',)

    @admin.display(
        boolean=True,
        description='source',
    )
    def has_source(self, moment):
        return bool(moment.source)

    def text_content(self, moment):
        return Truncator(moment.content).chars(50)

    @admin.display(
        boolean=True,
        description='business',
    )
    def has_business(self, moment):
        return bool(moment.business_tag)

    @admin.display(
        boolean=True,
        description='url',
    )
    def has_url(self, moment):
        return bool(moment.url_tag)

    @admin.display(
        boolean=True,
        description='location',
    )
    def has_location(self, moment):
        return bool(moment.location_tag)


@admin.register(UserMoment)
class UserMomentAdmin(MomentAdmin):
    list_display = MomentAdmin.list_display


@admin.register(EventMoment)
class EventMomentAdmin(admin.ModelAdmin):
    list_display = ('id', 'business')


@admin.register(EventMomentSlice)
class EventMomentSliceAdmin(admin.ModelAdmin):
    list_display = ("id",)
