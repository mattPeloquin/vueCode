#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Login utilities
"""
from django.conf import settings
from django.core.cache import caches
from django.contrib.auth import logout as django_logout

from mpframework.common import log
from mpframework.common.utils import now

_cache = caches['request']


def logout_user( request ):
    """
    Add to Django logout to set MPF visitor
    """
    django_logout( request )
    from ..models.visitor import Visitor
    request.user = Visitor( request )
    log.info2("LOGOUT programatic: %s -> %s", request.mpipname, request.user)


"""--------------------------------------------------------------------
    Login Failure Throttle

    Use a progressive timer increase to allow for login fails
    while also protecting against attacks

    BASED ON EMAIL WITHOUT SANDBOX
    This is based on email used in the login screen vs. tracking
    a particular user -- even though the same email could be used in
    different sandboxes, email is locked out across the entire system.
    Most legitimate emails would only be associated with a small number of sandboxes,
    so shouldn't have a negative impact of tenants impacting each other.
    Using email alone limits probing that might go across subdomains
    by ensures password throttle looks same regardless of whether
    the username is valid or not.
"""

def _login_throttle_key( email ):
    return '-'.join([ 'LOGIN_FAIL', email ])


def login_throttle_set( email ):
    """
    When login fails, record event in cache for processing in throttle below
    """
    key = _login_throttle_key( email )

    values = _cache.get( key )
    failures = values[1] + 1 if values else 1

    log.debug("Login throttle fail set: %s -> %s failures", email, failures)
    _cache.set( key, ( now(), failures ), settings.MP_LOGIN_FAILURE_WAIT )


def login_throttle_check( request ):
    """
    Returns true if login should be throttled, false if it should not
    """
    sandbox = request.sandbox
    email = request.POST.get( 'email', None )

    # Can't throttle (or login) a visitor login
    if not email:
        return

    try:
        values = _cache.get( _login_throttle_key( email ))
        log.debug2("Login throttle fail check: %s", values)

        if values:
            time_mark, failures = values

            if failures > settings.MP_LOGIN_FAILURE_MAX:
                # If max login failures are triggered, locked out until cache timeout
                log.info("USER LOGIN FAIL EXCEEDED: %s -> %s", sandbox, email)
                return True

            elif failures > settings.MP_LOGIN_FAILURE_THRESHOLD:
                # Once threshold is triggered, if delay is greater than difference in time between
                # the last login and this one, reject the login
                time_passed = ( now() - time_mark ).total_seconds()
                delay = (failures - settings.MP_LOGIN_FAILURE_THRESHOLD) * settings.MP_LOGIN_FAILURE_MULTIPLIER
                if time_passed < delay:
                    log.info("USER LOGIN THROTTLE DELAY %s -> %s, %s -> ( %s < %s )",
                             request.ip, sandbox, email, time_passed, delay)
                    return True

    except Exception:
        log.exception("Throttling login: %s", email)
