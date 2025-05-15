# myapp/models.py
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from datetime import timedelta


class UserManager(BaseUserManager):
    def create_user(self, email, phone_number, full_name, password=None):
        if not phone_number:
            raise ValueError('Users must have an phone number')
        user = self.model(
            email=self.normalize_email(email),
            phone_number=phone_number,
            full_name=full_name,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    

class User(AbstractUser):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15, unique=True)
    firebase_uid = models.CharField(max_length=128, unique=True, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_phone_verified = models.BooleanField(default=False)

    objects = UserManager()

    # USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone_number', 'full_name']

    def __str__(self):
        return self.email


class DeviceSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='device_sessions')
    refresh_token = models.TextField()
    device_name = models.CharField(max_length=255)
    device_ip = models.GenericIPAddressField(null=True, blank=True)
    device_location = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.user.email} - {self.device_name}"
    

