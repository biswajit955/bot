# security/firebase_init.py
import firebase_admin
from firebase_admin import credentials

from django.conf import settings
import os

# Prevent duplicate initialization
if not firebase_admin._apps:
    cred_path = os.path.join(settings.BASE_DIR, 'security/serviceAccountKey.json')
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
