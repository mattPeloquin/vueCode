#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Sitebuilder middleware
"""

from mpframework.common import log
from mpframework.common.middleware import mpMiddlewareBase

from .request_skin import RequestSkin


class SitebuilderMiddleware( mpMiddlewareBase ):
    """
    Setup portal configuration for the request based on the URL
    requested and portal configuration.
    """

    def process_request( self, request ):
        """
        Always load request skin for non-API calls as admin and other
        screens may use some theme elements from the skin.
        """
        if request.is_lite or request.is_api or request.is_bad:
            return

        request.skin = RequestSkin( request.sandbox )

        log.debug2("Set request skin %s: %s", request.ip, request.skin)
