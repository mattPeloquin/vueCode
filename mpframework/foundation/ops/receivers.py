#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Ops signal receivers
"""
from django.dispatch import receiver

from .signals import startup_signal
from .process_start import process_startup


@receiver( startup_signal )
def handle_startup( sender, **kwargs ):
    """
    Once Django is started, do any one-time server init
    Django.models will not be in place until this is called
    """
    process_startup()
