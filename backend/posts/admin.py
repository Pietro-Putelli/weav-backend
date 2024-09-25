from django.contrib import admin

from posts.models import BusinessPostSlice, BusinessPost, UserPost

admin_site = admin.site


@admin.register(UserPost)
class UserPostAdmin(admin.ModelAdmin):
    list_display = ("id", "profile", "title", "content")


@admin.register(BusinessPost)
class BusinessPostAdmin(admin.ModelAdmin):
    list_display = ("id", "business", "ordering")


@admin.register(BusinessPostSlice)
class BusinessPostSliceAdmin(admin.ModelAdmin):
    list_display = ("get_venue", "id", "title", "content")

    @admin.display(
        description="venue",
    )
    def get_venue(self, slice):
        return slice.post.business.name
