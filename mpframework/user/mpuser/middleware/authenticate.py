#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Override Django User Authentication
"""
from django.conf import settings
from django.contrib import auth

from mpframework.common import log
from mpframework.common.middleware import mpMiddlewareBase

from ..models.visitor import Visitor


# Backend is stateless, and MPF only uses one,
# so load it for each process instead of on each request
backend = auth.load_backend( settings.MP_USER_AUTHENTICATION_BACKEND )


class mpAuthenticationMiddleware( mpMiddlewareBase ):
    """
    Attach an mpUser or Visitor to the request.

    Since user is always used, don't bother with lazy caching, and
    add information for logging.

    Adjust staff level for special situations related to allowed staff
    level changing for provider or sandbox.
    """

    def process_request( self, request ):
        """
        Attach user to the request
        """
        if request.is_bad:
            return
        user = self._get_user( request )

        request.user = user
        request.mpname = user.log_name
        request.mpipname = 's{} {} {}'.format( request.sandbox.pk, request.ip, user.email )
        request.mpremote = request.META.get('REMOTE_ADDR')

        if not request.is_lite:
            log.info4("Request user -> %s", request.mpipname)

    @staticmethod
    def _get_user( request ):
        """
        Replaces Django delegation to authentication backend to include
        passing the sandbox to get_user.
        """
        if request.session:
            try:
                error = None
                # Django login adds user ID to auth.SESSION_KEY
                user_id = request.session.get( auth.SESSION_KEY )
                if user_id:
                    user = backend.get_user( user_id, request.sandbox )
                    if user:
                        return user

                    error = "no user found for %s" % user_id

            except Exception as e:
                if settings.MP_DEV_EXCEPTION:
                    raise
                error = e
            if error:
                log.warning("Can't get user from request: %s", error)

        return Visitor( request )
