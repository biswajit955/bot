# myapp/urls.py
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import SendOTP, VerifyOTP, RegisterView, LogoutView

urlpatterns = [
    path('auth/token/',TokenObtainPairView.as_view(),name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(),name='token_refresh'),
    path('auth/send-otp/', SendOTP.as_view(),   name='send_otp'),
    path('auth/verify-otp/', VerifyOTP.as_view(), name='verify_otp'),
    path('auth/register/', RegisterView.as_view(),   name='register'),
    path('auth/log-out/', LogoutView.as_view(), name='log_out'),
]
