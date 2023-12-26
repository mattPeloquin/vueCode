#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Replace Django clickjacking middleware with CSP and
    legacy XFRAME support specific to MPF.

    FUTURE - could get more specific with CSP rules, but is tricky
    because customers need to drop styles and scripting onto pages.
"""
from django.conf import settings

from mpframework.common.middleware import mpMiddlewareBase

from ..csp import *


CSP_DEFAULT = "frame-ancestors 'self'"
CSP_SITE = "frame-ancestors 'self' {0}://{1} {0}://*.{2}"
CSP_ANY = "frame-ancestors *"


class mpCspMiddleware( mpMiddlewareBase ):
    """
    Add MPF iframe embedding directives based on the type of page.
    The default is NO iframe access, with iframe_allow decorator
    allowing embedding.
    """

    def process_response( self, request, response ):
        if request.is_healthcheck or request.is_bad:
            return response

        if request.iframe_allow == CSP_IFRAME_ANY:
            response.headers['Content-Security-Policy'] = CSP_ANY

        elif request.iframe_allow == CSP_IFRAME_SITE:
            response.headers['Content-Security-Policy'] = CSP_SITE.format(
                        request.scheme, request.host, settings.MP_ROOT['HOST'] )

        elif not request.is_api:
            response.headers['Content-Security-Policy'] = CSP_DEFAULT
            response.headers['X-Frame-Options'] = 'DENY'

        return response
    