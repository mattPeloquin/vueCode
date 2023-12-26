#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Exception response processing
"""
import sys
from django import http
from django.conf import settings
from django.core.exceptions import ( ObjectDoesNotExist, PermissionDenied,
            DisallowedHost )
from mpframework.common import log
from mpframework.common.middleware import mpMiddlewareBase
from mpframework.testing.framework import mpTestingException

from ..views.errors import handle_400


class mpExceptionMiddleware( mpMiddlewareBase ):
    """
    Unhandled exception handling for request view processing.
    Returns error page or None (in which case Django calls handle_500)
    """
    def process_exception( self, request, exception ):
        """
        MPF middleware exception processing is run first
        on all exceptions that occur when Django handles a request.
        """
        try:
            # Swallow any test-specific exceptions during testing
            if settings.MP_TESTING:
                if isinstance( exception, mpTestingException ):
                    log.debug2("Swallowing mpTestingException")
                    return handle_400( request, exception )

            """
            Standard 404 response
            SECURE - MPF uses 404 exceptions as standard for bailing on requests
            that can't be completed but are not error conditions; the goal is
            to limit probling by providing minimal info.
            """
            if isinstance( exception, ( http.Http404, ) ):
                log.debug("Returning 400 page for 404 exception: %s", exception)
                return handle_400( request, exception, status=404 )

            """
            Transform some exceptions into 400s
            Could be caused by attacks, programming errors or bad data; make it
            look a 404 to the user, but log warning.
            Negative tests will trigger, so attenuate warning in testing.
            """
            if isinstance( exception, ( KeyError, ObjectDoesNotExist,
                    PermissionDenied, DisallowedHost,
                    http.HttpResponseBadRequest, http.HttpResponseNotFound,
                    http.HttpResponseForbidden, http.HttpResponseNotAllowed,
                    http.HttpResponseGone ) ):
                msg = "VIEW EXCEPTION 400 %s(%s) -> %s, %s" % (
                        type(exception), exception, request.mpipname, request.uri )
                # Avoid error emails for negative testing, stop tests for positive testing
                if settings.MP_TESTING:
                    if request.mptest['fail']:
                        log.info( msg )
                    else:
                        log.info_stack( exc=exception )
                        sys.exit(1)
                else:
                    log.warning( msg )
                # Let Django debug page handle exception for debugging
                if settings.DEBUG:
                    log.debug_stack( depth=12, exc=exception )
                    return

                return handle_400( request, exception )

            """
            Otherwise mark request as bad, log, and return 500.
            This is either a programming error or server problem like a DB
            connection time out (which for example should have been handled
            earlier by a db_connection_retry decorator).
            """
            request.is_bad = True
            if not settings.MP_TESTING:
                log.warning("VIEW EXCEPTION 500 %s: %s -> %s",
                        request.mpipname, exception, request.uri )

        except Exception as e:
            # Don't make a fuss if something fails in attempt to get info
            log.exception("handling VIEW exception: %s -> %s -> %s",
                            request.mpipname, request.uri, exception)

        if settings.MP_TESTING:
            if request.mptest['fail']:
                return handle_400( request, exception )
            else:
                log.info_stack( depth=12, exc=exception )
        else:
            log.debug_stack( depth=24, exc=exception )
