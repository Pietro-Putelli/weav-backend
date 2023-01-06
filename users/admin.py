from django.contrib import admin
from users.models import User, RegistrationToken

admin.site.register(User)
admin.site.register(RegistrationToken)
