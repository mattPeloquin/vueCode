#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Failed Login
"""

from django.dispatch import receiver
from django.contrib.auth.signals import user_login_failed

from mpframework.common import log

from ..utils.login import login_throttle_set


@receiver( user_login_failed )
def handle_user_login_failed( sender, **kwargs ):
    """
    Log login failures and collect data in cache for throttling
    """
    try:
        log.debug("Login failed: %s", kwargs)

        credentials = kwargs['credentials']   # Throw exception if no credentials
        username = credentials.get('username')
        if username:
            login_throttle_set( username )

    except Exception as e:
        # Not critical, so if a problem with credentials, just log
        log.error("Error handling login failure: %s", e)
