#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Logout support
"""
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_out

from mpframework.common import log


@receiver( user_logged_out )
def handle_user_logged_out( sender, **kwargs ):
    user = kwargs.get('user')
    log.debug("Logout event occurred for: %s", user)

    if user:
        log.info2("LOGOUT: %s", user.log_name)

        if user.is_staff:
            # Reset user test mode to avoid confusion on next login
            user.staff_user_view = False
            user.save()
