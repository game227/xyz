"""ASGI config for XYZ.

Jonli efir WebRTC/WebSocket orqali emas, tashqi havola (YouTube/Telegram)
orqali ishlaydi — shuning uchun alohida WebSocket marshrutlash kerak emas.
Daphne shunchaki oddiy Django ASGI ilovasini xizmat qiladi.
"""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_asgi_application()
