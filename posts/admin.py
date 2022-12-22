from django.contrib import admin

from posts.models import BusinessPostSlice, BusinessPost, UserPost, UserPostSlice

admin_site = admin.site


@admin.register(UserPost)
class UserPostAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "ordering")


@admin.register(UserPostSlice)
class UserPostSliceAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "content")


@admin.register(BusinessPost)
class BusinessPostAdmin(admin.ModelAdmin):
    list_display = ("id", "business", "ordering")


@admin.register(BusinessPostSlice)
class BusinessPostSliceAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "content")
