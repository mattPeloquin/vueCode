#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    User tracking middleware support
"""
from django.conf import settings

from mpframework.common.middleware import mpMiddlewareBase

from ..tracking_update import update_for_request


class UserTrackingMiddleware( mpMiddlewareBase ):
    """
    Tracking Users via Middleware request handling

    Implements user session and reporting tracking on UI requests,
    with capability to tune for scalability (any data collected
    here is optional and not required for core operation)

    This middleware assumes session tracking is turned on and
    only works with authenticated users (vs. visitor tracking)
    """

    def process_request( self, request ):
        """
        Handle tracking for requests and store in user
        """
        if request.mppath.startswith( settings.MP_URL_TRACKING_EXCLUDES ):
            return

        update_for_request( request )
