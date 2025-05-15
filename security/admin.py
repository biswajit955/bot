from django.contrib import admin
from security.models import User, DeviceSession
# Register your models here.

admin.site.register(User)
admin.site.register(DeviceSession)