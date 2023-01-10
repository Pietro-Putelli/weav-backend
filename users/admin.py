from django.contrib import admin
from users.models import User, AccessToken

admin.site.register(User)
admin.site.register(AccessToken)
