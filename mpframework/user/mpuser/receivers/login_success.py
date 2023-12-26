#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Successful Login
"""
from django.conf import settings
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in

from mpframework.common import log
from mpframework.common.events import sandbox_event


@receiver( user_logged_in )
def handle_user_logged_in( **kwargs ):
    """
    Sent by Django on login
    """
    request = kwargs['request']  # Throw exception if no request
    user = kwargs.get('user')
    if not user:
        log.error("ATTEMPT TO LOGIN NULL USER")
        return
    try:
        # Put user id with session for sanity check
        request.session['user_id'] = user.pk

        if settings.MP_TESTING:
            # TESTING - When running view tests, the request isn't fully formed,
            # so does not have host_url set such that sandbox can be detected
            # sandbox will be set in test code
            log.debug2("LOGIN (TESTING) %s", user)
            return

        log.info("USER LOGIN %s -> %s, %s", user.log_name, request.mpipname,
                    request.session.session_key)
        sandbox = request.sandbox
        sandbox_event( user, 'user_login', sandbox )

        # Put current sandbox in session to support session reduction
        request.session['sandbox_id'] = sandbox.pk

        # Update the rest of user metrics
        user.health_check( sandbox )

    except Exception:
        log.exception("Problem with user login: %s", request.mpipname)
        if settings.MP_TESTING:
            raise
