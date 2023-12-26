#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Support CORS-specific request/response handling

    FUTURE SECURE - fetch metadata support
"""
from django.conf import settings
from django.http import HttpResponse
from django.views.defaults import bad_request

from mpframework.common import log
from mpframework.common.middleware import mpMiddlewareBase


_allow_headers = settings.MP_HTTP_SECURITY['CORS_HEADERS']
_max_age = settings.MP_HTTP_SECURITY.get('CORS_MAX_AGE')


class mpCorsMiddleware( mpMiddlewareBase ):
    """
    MPF CORS processing occurs before other security processing
    to allow short-circuiting preflight.
    """

    def process_request( self, request ):
        if request.is_healthcheck or request.is_bad:
            return

        # Short-circuit CORS preflight requests
        if 'OPTIONS' == request.method:
            response = HttpResponse()
            log.info3("CORS PREFLIGHT request: %s", request.mpipname)
            return response

        # Note if this is a CORS request
        origin = request.META.get('HTTP_ORIGIN')
        request.mpcors = bool( origin )
        if request.mpcors:
            log.debug("CORS request %s: %s://%s -> %s", request.mpipname,
                        request.scheme, request.host, origin )
            request.mpcors_origin = origin

            # Guard against malformed origins like 'null'
            try:
                request.mpcors_host = origin.split('//')[1]
            except Exception:
                request.is_bad = True
                log.warning("SUSPECT - Invalid CORS origin %s %s -> %s",
                            request.mpipname, request.uri, origin)
                return bad_request( request, Exception() )

            # Optionally validate origin by checking end of host against
            # configured names
            if settings.MP_ROOT['CORS_HOSTS']:
                if request.host != request.mpcors_host:
                    request.mpcors_diff_origins = True

                    if not any([ request.host.endswith( known ) for known in
                                settings.MP_ROOT['CORS_HOSTS'] ]):
                        request.is_bad = True
                        log.warning("SUSPECT - Bad CORS origin %s %s -> %s",
                                    request.mpipname, request.uri, origin)
                        return bad_request( request, Exception() )

                    log.debug2("CORS different origin request: %s, %s",
                                request.mpname, request.mpcors_origin )

    def process_response( self, request, response ):
        """
        Handle CORS access responses
        """
        if not getattr( request, 'mpcors', None ) or request.is_bad:
            return response

        # Always send approved origin credentials, even with
        # requests that are not strictly CORS (like POSTs) to
        # ensure compatibility
        response['access-control-allow-origin'] = request.mpcors_origin
        response['access-control-allow-credentials'] = 'true'

        # Preflight stuff
        if 'OPTIONS' == request.method:
            response['access-control-allow-methods'] = 'GET,POST,OPTIONS,PATCH,PUT'

            headers = request.META.get('HTTP_ACCESS_CONTROL_REQUEST_HEADERS')
            if headers:
                headers = headers.lower().split(',')
                allowed_headers = []
                for header in headers:
                    if header in _allow_headers:
                        allowed_headers.append( header )
                response['access-control-allow-headers'] = ','.join( allowed_headers )

            if _max_age:
                response['access-control-max-age'] = _max_age

        log.debug2("CORS response: %s, %s", request.mpname, request.mpcors_origin)
        return response
