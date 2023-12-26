#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    First request, last response middleware
"""
from django.conf import settings
from django.core.cache import caches
from django.views.defaults import bad_request

from mpframework.common import log
from mpframework.common import sys_options
from mpframework.common.ip_throttle import check_ip_limiting
from mpframework.common.middleware import mpMiddlewareBase
from mpframework.common.db.connections import open_connections
from mpframework.common.logging.timing import mpTiming
from mpframework.common.logging.timing import mpTimingNone
from mpframework.common.utils import epoch_ms
from mpframework.common.utils import get_random_key
from mpframework.common.utils.request import is_api_request
from mpframework.common.utils.request import get_ip
from mpframework.common.utils.request import get_referrer
from mpframework.common.utils.request import QUERYSTRING_PREFIX
from mpframework.common.utils.request import QUERYSTRING_POPUP


class mpFirstLastMiddleware( mpMiddlewareBase ):
    """
    Ensure MPF has first and last word on request-response chain
    """

    # Allow some headers to be set by request
    HEADER_OVERRIDES = [
        # FUTURE - decide whether to always honor cache control from client
        # ('HTTP_CACHE_CONTROL', 'cache-control')
        ]

    def process_request( self, request ):
        """
        First handling of requests, defines MPF request assumptions:
          - MPF additions to request object
          - Banning and throttling
          - Invalid host - Sites are probed in various ways; downgrade
            Django invalid host handling to avoid noisy warnings
          - HTTP emulation for PUT/DELETE
          - Standard per-request logging timing
        """

        # Add timing info to request, either active object or dummy placeholder
        request.mptiming = mpTiming( db=( log.info_on() > 1 )
                            ) if log.info_on() else mpTimingNone()

        # Add unique identifier to request object so it looks like
        # a model FOR CURRENT PROCESS caching/memoization hash
        request.id = id( request )

        # Add some frequently used information
        request.ip = get_ip( request )
        request.mppath = request.path.strip('/ ')
        request.mppathsegs = request.mppath.split('/')
        request.mpname = request.ip
        request.mpipname = request.ip

        # Ensure request objects have assumed MPF attributes
        request.is_bad = False
        request.is_healthcheck = False
        request.is_lite = False
        request.mpinfo = {}

        request.sandbox = None
        request.user = None
        request.skin = None
        request.mperror = ''
        request.iframe_allow = False

        request.is_portal = False
        request.is_portal_content = False
        request.is_page_admin = False
        request.is_page_staff = False
        request.is_proxy = False
        request.is_popup = False
        request.is_popup_close = False

        # Instead of old Django is_ajax, mark all non-text html response as api
        request.is_api = is_api_request( request )

        # Per-request stash, temporary data during request not worth caching
        request.mpstash = {}

        # Malformed IPs won't be accepted; shouldn't happen in legit cases
        if not request.ip:
            request.mpipname = 'noIP'
            return _bad_request( request, "Request with No IP" )

        # Bail if the IP is throttled/banned
        throttled = check_ip_limiting( request.ip )
        if throttled:
            return _bad_request( request, throttled )

        # Store host as part of the request; don't go forward if host is
        # malformed - note that "no-host" requests should have a host so not
        # trigger this, their host is just not their sandbox
        # Convert denied host exception into a logging event (vs. Django email)
        try:
            request.host = request.get_host()
        except Exception as e:
            return _bad_request( request, "Bad host {}".format(e) )

        log.timing2("START REQUEST MIDDLEWARE: %s", request.mptiming)

        # Items not used in bad requests
        request.path_full = request.get_full_path()[:255]
        request.uri = request.host + request.path_full
        request.referrer = get_referrer( request )

        # Special case some URLs that don't need full processing
        if request.mppath.startswith( settings.MP_HEALTHCHECK_URL ):
            request.is_healthcheck = True
        request.is_lite = request.is_healthcheck or request.mppath.startswith(
                settings.MP_URL_LITE_EXCLUDES )

        # Special case healthcheck
        if request.is_healthcheck:
            request.META['HTTP_HOST'] = settings.MP_HEALTHCHECK_HOST
            request.host = settings.MP_HEALTHCHECK_HOST
            request.mpname = 'HealthCheck'
            return

        log.debug_on() and log.debug("%s> %s %s %s", request.mptiming.pk,
                    request.mpipname, request.method, request.uri)

        # Setup request info pushed to cache in response for tracking/debugging
        request.mpinfo = _start_request_info( request )

        # Determine admin page from paths since always well-defined
        request.is_page_admin = request.mppath.startswith(
                    settings.MP_URL_ADMIN_PAGES )
        request.is_page_staff = request.is_page_admin

        # Convenience for detecting popup windows
        request.is_popup = ( QUERYSTRING_POPUP in request.GET or
                    QUERYSTRING_POPUP in request.POST )
        popup_close = QUERYSTRING_PREFIX + 'popup_close'
        request.is_popup_close = ( popup_close in request.GET or
                    popup_close in request.POST )

        # Support HTTP emulation of newer request PUT, etc. methods
        override_method = request.META.get('HTTP_X_HTTP_METHOD_OVERRIDE')
        if override_method:
            log.debug2("X-HTTP method override: %s -> %s", request.method, override_method)
            request.method = override_method

    def process_response( self, request, response ):
        """
        Last handling of responses:
          - Modification to Django Vary header to not use cookie
          - Add any supported request headings
          - Timing logging for requests
        """
        if request.is_healthcheck or request.is_bad:
            return response

        # Remove Django global vary header on cookie; vary will be
        # modified for specifc cases when needed
        # HACK - Session middleware adds vary on cookie, but uses lowercase
        if response.get('vary'):
            varies = response['vary'].split(',')
            try:
                varies.remove('Cookie')
            except ValueError:
                pass
            if varies:
                response['vary'] = ','.join( varies )
            else:
                del response['vary']

        # Allow some headers to be set on request
        for request_name, response_name in self.HEADER_OVERRIDES:
            request_header = request.META.get( request_name )
            if request_header:
                response[ response_name ] = request_header

        # Support for request/response tracking/debugging
        _add_mpinfo( request, response )

        _log_end( request, response )
        return response

def _bad_request( request, msg ):
    request.is_bad = True
    log.info2("<x SUSPECT - BAD_REQUEST %s: %s -> %s %s %s", msg, request.ip,
                request.META.get('REQUEST_METHOD'), request.META.get('HTTP_HOST'),
                request.META.get('REQUEST_URI') )
    return bad_request( request, Exception() )

"""
    Stash information about request into cache for tracking and debug.
    A unique request tag is also used in some cases to uniquely identify
    requests and to punch through caching.
    For tracking the request key is kept short for easier human reading; due
    to birthday paradox at 6 there is 1% chance of conflict at 30K entries,
    but ok since time window is short, and consequence of conflict are low.
"""
_INFO_LIFESPAN = 14400  # 4 hours

def _start_request_info( request ):
    if sys_options.disable_non_critical():
        return {}
    if request.is_api or not sys_options.flags().get('TRACKING_requests'):
        return {
            'tag': get_random_key( 8, prefix='rq_' ),
            }
    return {
        'tag': get_random_key( 6, prefix='rqt_' ),
        'user': request.mpipname,
        'uri': request.uri,
        'response_type': 'page',     # May be overridden downstream
        'method': request.method,
        'start_ms': epoch_ms(),
        }

def _add_mpinfo( request, response ):
    if not request.mpinfo or not sys_options.flags().get('TRACKING_requests'):
        return
    request.mpinfo['send_ms'] = epoch_ms()
    # Response type
    typ = request.mpinfo.get('response_type')
    if typ:
        response['mpf-response'] = typ
    # Mark cached tag for tracking
    tag = request.mpinfo.get('tag')
    if tag:
        caches['request'].set( tag, request.mpinfo, _INFO_LIFESPAN )
        response['mpf-tag'] = tag
    # Pass outcome back for nginx/header
    result = request.mpinfo.get('result')
    if result:
        response['mpf-result'] = result

"""
    Key display of requests for info and debugging logging
    Info goal is for human reading and searching AND log analysis.
"""
def _log_end( request, response ):
    if not log.info_on() > 1 or settings.MP_TEST_NO_LOG:
        return
    try:
        rt = request.mptiming

        # Request log line prefix to support
        # seeing and searching on for key request types
        sym = '-' if request.is_api else '<' if request.is_proxy else '='
        sym += '+' if request.is_proxy else '<'
        if log.debug_on():
            sym = request.mptiming.pk + sym

        # Make prefix quick lookup information
        if request.mperror:
            prefix = request.mperror
        else:
            prefix = '' if request.is_proxy else _log_duration( rt.total )

        # Capture the key information about the request
        info = []
        if log.debug_on():
            info.append( 'c' + str(len( open_connections() )) )
        info.extend([ request.mpipname, request.method,
                        str(response.status_code),
                        request.mpinfo.get( 'result', '' ),
                        ])
        info = ' '.join( info )
        redirect = getattr( response, 'url', '' )

        # Add details
        detail = '"{}"'.format( request.uri )
        if getattr( request, 'mpcors', None ):
            detail += ' CORS '
            if getattr( request, 'mpcors_diff_origins', None ):
                detail += request.mpcors_origin
        if request.mpinfo.get('tag'):
            detail += ' ' + request.mpinfo.get('tag')
        # Add HTTP header info for all errors (attack insight) and higher logging
        # Rely on header max size to prevent wasting too much time here
        if request.mperror or log.debug_on() > 2:
            seperator = '\n' if log.debug_on() else ' | '
            headers = [ '', 'REQUEST HEADERS:' ]
            for name, value in request.META.items():
                if name.startswith('HTTP_'):
                    headers.append( "{}:{}".format( name[5:], value ) )
            detail += seperator.join( headers )
        if log.debug_on() > 3:
            headers = [ '', 'RESPONSE HEADERS:' ]
            for name, value in response.items():
                headers.append( "{}:{}".format( name, value ) )
            detail += '\n'.join( headers )

        log.info2("%s %s %s %s %s %s", sym, prefix, rt.log_row, info, detail, redirect)

        if log.debug_on():
            content_bytes = len( getattr( response, 'content', '' ) )
            log.debug_values("RESPONSE %s bytes: %s -> %s",
                                    content_bytes, request.uri, response )
    except Exception:
        log.exception("FirstLast log_end: %s", getattr(request, 'uri', 'BAD_REQUEST'))

# Provide different qualifiers in log for easy performance searches

def _log_duration( duration ):
    speed = 'FASTX'
    if _modifier:
        duration = duration / _modifier
    if duration > 0.05:
        speed = 'FAST'
        if duration > 0.20:
            speed = 'SLOW'
            if duration > 0.50:
                speed = 'SLOWX'
                if duration > 1.0:
                    speed = 'SLOWXX'
                    if duration > 4.0:
                        speed = 'SLOWXXX'
    return speed

_modifier = None
if settings.MP_PROFILE in [ 'prod-boh', 'prod-ft' ]:
    _modifier = 3.0
