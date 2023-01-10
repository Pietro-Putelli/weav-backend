from django.contrib import admin

from chances.models import UserChance


@admin.register(UserChance)
class UserChanceAdmin(admin.ModelAdmin):
    list_display = ("id", "first", "second")
