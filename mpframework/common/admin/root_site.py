#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Root staff admin
"""

from django.conf import settings
from django.http import Http404

from .. import log
from ..utils import request_is_authenticated
from ..utils.login import redirect_login
from .base import BaseAdminSite


class RootAdminSite( BaseAdminSite ):
    """
    The root admin site is basically the normal DJ admin
    """

    def has_permission( self, request ):
        """
        Only root users have access to the root admin
        """
        if request_is_authenticated( request ):
            user = request.user
            try:
                if user.access_root:
                    if not settings.MP_TESTING:
                        log.info("ROOT ACCESS: %s -> %s", request.mpipname, request.uri)
                    return True

                log.warning("ROOT SITE VIOLATION: %s -> %s", request.mpipname, request.uri)
            except Exception:
                if settings.MP_DEV_EXCEPTION:
                    raise
                log.exception("ROOT permission: %s -> %s", request.mpipname, request.uri)

            # Raise 404 so these cases don't look any different than a random URL
            raise Http404

        return False

    def login( self, request, _extra_context=None ):
        """
        Take any failures to portal/login
        """
        return redirect_login( request )

root_admin = RootAdminSite( name='root_admin' )
