#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    LMS signal receivers
"""
from django.conf import settings
from django.dispatch import receiver

from mpframework.foundation.ops.signals import startup_signal


@receiver( startup_signal )
def handle_startup( sender, **kwargs ):
    """
    On startup may want to prewarm stories by trying to mount all of them
    """
    if not settings.MP_IS_DJ_SERVER:
        from .models import Package
        Package.objects.prewarm()
