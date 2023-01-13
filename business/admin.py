from django.contrib import admin

from business.models import Business, BusinessToken


@admin.action(description='Mark selected business as approved')
def approve_business(_, __, queryset):
    queryset.update(is_approved=True)


@admin.register(Business)
class NotApprovedBusiness(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'is_approved', 'get_type', 'created_at')
    list_filter = ('is_approved',)
    actions = [approve_business]

    def get_type(self, business):
        if business.location is None:
            return "event"
        return "venue"


@admin.register(BusinessToken)
class BusinessTokenAdmin(admin.ModelAdmin):
    list_display = ('business', 'key')
