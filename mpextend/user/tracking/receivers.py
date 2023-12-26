#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Extended user receivers
"""
from django.conf import settings
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in

from .tracking_update import update_for_request


@receiver( user_logged_in )
def handle_user_logged_in( **kwargs ):
    """
    Update tracking metrics on login, which will also
    trigger a session reduction if user has exceeded sessions.
    """
    request = kwargs['request']  # Throw exception if no request
    update_for_request( request, new_login=True )
