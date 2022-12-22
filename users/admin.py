from django.contrib import admin
from users.models import TokenCode, User

admin.site.register(User)
admin.site.register(TokenCode)
