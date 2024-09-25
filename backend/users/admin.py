from django.contrib import admin
from users.models import User, AccessToken


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    readonly_fields = ("uuid",)
    list_display = ("name", "phone", "superuser",)

    @admin.display(
        boolean=True,
        description='superuser',
    )
    def superuser(self, user):
        return user.is_superuser


admin.site.register(AccessToken)
