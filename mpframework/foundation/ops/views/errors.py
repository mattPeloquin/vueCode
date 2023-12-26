#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    4xx/5xx handling
    Instead of providing information from django in error pages, pass errors
    back to nginx to display simple status pages to discourage probing.
    Debugging should be handled through logging.
"""
import sys
from django.contrib.staticfiles.views import serve

from mpframework.common import log
from mpframework.common.utils import join_urls

from ..csp import iframe_allow_any


def handle_500( request ):
    try:
        typ, val, traceback = sys.exc_info()
        log.info2("HTTP 500: %s -> %s, %s", _request_info( request ), typ, val )
        if not request.is_bad:
            log.debug_stack()
    except Exception:
        log.exception("LOGGING 500")
    return _request_error_handler( request, 500 )

@iframe_allow_any
def handle_400( request, exception, status=400 ):
    """
    MAP ALL 400 errors to 404s
    Prevents easy leakage of sessions and url structure
    """
    if status != 404:
        log.info2("HTTP %s returning 404: %s", status, _request_info( request ))
    log.debug("400 HANDLER EXCEPTION: %s", exception)
    return _request_error_handler( request, 404 )

def handle_403( request, exception ):
    return handle_400( request, exception, 403 )

def handle_404( request, exception ):
    return handle_400( request, exception, 404 )

def _request_error_handler( request, status ):
    """
    Send empty error response back to nginx and let it handle page display.
    Some 404 are handled at nginx (paths that aren't passed to Django),
    which should look the same as these responses to avoid any leaking of urls.
    """
    path = join_urls( 'mpf-root', '4xx.htm' if status == 404 else '5xx.htm' )
    response = serve( request, path, insecure=True )
    response.status_code = status
    return response

def _request_info( request ):
    # Don't assume FirstLast processing has been used here
    try:
        ipname = request.mpipname
    except Exception:
        ipname = ''
    try:
        url = request.build_absolute_uri()
    except Exception:
        url = request.path
    return "{} {} {}".format( ipname, request.method, url )
