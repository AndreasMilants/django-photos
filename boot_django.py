import os
import django
from django.conf import settings
from django_photos.django_photos.settings import get_settings


def boot_django():
    settings.configure(
        ** get_settings()
    )

    django.setup()
