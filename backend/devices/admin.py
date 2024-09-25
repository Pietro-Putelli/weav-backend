from django.contrib import admin
from devices.models import Device


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("user", "token", "is_stronzo")

    @admin.display(
        boolean=True,
        description='stronzo',
    )
    def is_stronzo(self, device):
        return device.token is None
