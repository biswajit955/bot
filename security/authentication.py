from rest_framework import authentication, exceptions
import firebase_admin
from firebase_admin import auth
from .models import User

class FirebaseAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION")
        if not auth_header:
            raise exceptions.AuthenticationFailed("No auth token provided")
        
        try:
            id_token = auth_header.split(" ")[1]
        except IndexError:
            raise exceptions.AuthenticationFailed("Invalid Authorization header format")

        try:
            decoded_token = auth.verify_id_token(id_token)
        except Exception as e:
            raise exceptions.AuthenticationFailed(f"Invalid auth token: {str(e)}")

        phone_number = decoded_token.get("phone_number")
        if not phone_number:
            raise exceptions.AuthenticationFailed("Phone number not found in token")

        user, created = User.objects.get_or_create(phone_number=phone_number)
        return (user, None)