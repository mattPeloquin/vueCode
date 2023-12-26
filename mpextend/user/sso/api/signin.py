#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    User Content API views
"""

from mpframework.common import log
from mpframework.common.api import respond_api_call


def sso_signin( request ):
    """
    TBD SSO
    """
    def handler( payload ):
        user = request.user
        rv = { 'TBD': False }


        log.debug("%s ACCESS item complete: %s -> %s", request.mptiming,
                    request.mpipname, rv)
        return rv

    return respond_api_call( request, handler, methods=['POST'] )
