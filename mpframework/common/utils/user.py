#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    User utilities that only have dependency on Django
"""
from django.conf import settings


def session_cookie_name( sandbox ):
    """
    Add sandbox to cookie name to allow cookies to coexist on a common
    URL in some scenarios like no-host requests
    """
    rv = settings.SESSION_COOKIE_NAME.format( sandbox.pk )
    if settings.DEBUG:
        rv += 'debug'
    if settings.MP_TESTING:
        rv += 'test'
    return rv


def request_is_authenticated( request ):
    """
    Adds sandbox checking to request authentication for user
    """
    assert request.user and request.sandbox
    return bool( request.sandbox and request.user and
                 request.user.is_authenticated and
                 request.sandbox == request.user.sandbox
                 )
