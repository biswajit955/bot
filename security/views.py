import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from firebase_admin import auth as firebase_auth
from datetime import timedelta
from security.serializers import RegisterSerializer
from security.models import DeviceSession


User = get_user_model()

class SendOTP(APIView):
    """
    POST { "phone": "+15551234567", "recaptchaToken": "<token from frontend>" }
    → 200 { "sessionInfo": "..." }
    """
    def post(self, request):
        phone = request.data.get('phone')
        recaptcha = request.data.get('recaptchaToken')  # required by Firebase

        try:
            user = User.objects.get(phone_number=phone)
            if not phone or not recaptcha:
                return Response({'detail': 'phone and recaptchaToken required.'},
                                status=status.HTTP_400_BAD_REQUEST)

            url = f'https://identitytoolkit.googleapis.com/v1/accounts:sendVerificationCode?key={settings.FIREBASE_API_KEY}'
            payload = {
                'phoneNumber': phone,
                'recaptchaToken': recaptcha
            }
            resp = requests.post(url, json=payload)
            if resp.status_code != 200:
                return Response(resp.json(), status=resp.status_code)

            return Response(resp.json(), status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "User not found. Please complete signup first."}, status=404)


class VerifyOTP(APIView):
    """
    POST {
      "sessionInfo": "...",
      "code": "123456"
    }
    → 200 { "access": "...", "refresh": "...", "user": { … } }
    """
    def post(self, request):
        session_info = request.data.get('sessionInfo')
        code         = request.data.get('code')
        if not session_info or not code:
            return Response({'detail': 'sessionInfo and code required.'},
                            status=status.HTTP_400_BAD_REQUEST)

        url = f'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPhoneNumber?key={settings.FIREBASE_API_KEY}'
        payload = {
            'sessionInfo': session_info,
            'code':        code
        }
        resp = requests.post(url, json=payload)
        if resp.status_code != 200:
            return Response(resp.json(), status=resp.status_code)

        data = resp.json()
        phone_number = data['phoneNumber']
        firebase_uid = data['localId']

        # 2) Lookup existing user (must have registered already)
        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found. Complete signup first."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 3) Mark phone verified (only on first‐time verify)
        if not user.is_phone_verified:
            user.is_phone_verified = True
            user.firebase_uid      = firebase_uid
            user.save(update_fields=['is_phone_verified', 'firebase_uid'])

        # 4) Issue JWT tokens
        refresh = RefreshToken.for_user(user)

        # 5) Capture device info, IP, geo
        ip             = self.get_client_ip(request)
        user_agent     = request.META.get('HTTP_USER_AGENT', 'Unknown')
        location       = self.get_location_from_ip(ip)

        DeviceSession.objects.create(
            user=user,
            refresh_token=str(refresh),
            device_name=user_agent,
            device_ip=ip,
            device_location=location,
            expires_at=timezone.now() + timedelta(hours=24)
        )

        return Response({
            'full_name':user.full_name,
            'email':user.email,
            'phone_number':user.phone_number,
            'access':  str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_200_OK)
    
    def get_client_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        return xff.split(',')[0] if xff else request.META.get('REMOTE_ADDR')

    def get_location_from_ip(self, ip):
        try:
            r = requests.get(f'https://ipapi.co/{ip}/json/')
            j = r.json()
            return f"{j.get('city')}, {j.get('region')}, {j.get('country_name')}"
        except:
            return "Unknown"


class RegisterView(APIView):
    """
    POST {"full_name": "Biswajit Paloi", "email":"test@email.com" , "phone_number":"+911234567890","password":"zzzzzz10","confirm_password":"zzzzzz10"}    
    → 200 { "phone_no": "..." }
    """   
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"phone_no": serializer.data["phone_number"]}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({"error": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            DeviceSession.objects.filter(refresh_token=refresh_token).delete()
            return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

class HomeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        sessions = DeviceSession.objects.filter(user=user)

        session_data = []
        for s in sessions:
            session_data.append({
                "device": s.device_name,
                "ip": s.device_ip,
                "location": s.device_location,
                "created_at": s.created_at,
                "expires_at": s.expires_at,
                "is_expired": s.is_expired(),
            })

        return Response({
            "user": {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "phone": user.phone_number,
            },
            "active_sessions": session_data
        })
