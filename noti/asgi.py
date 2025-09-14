"""
ASGI config for noti project.
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'noti.settings.development')

application = get_asgi_application()
