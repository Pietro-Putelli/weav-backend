from django.contrib import admin
from users.models import User, AccessToken


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    readonly_fields = ("uuid",)


admin.site.register(AccessToken)
