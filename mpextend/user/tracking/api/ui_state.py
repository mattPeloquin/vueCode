#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    mpUser-related API views
"""

from mpframework.common import log
from mpframework.common.api import respond_api_call
from mpframework.common.view import login_required


@login_required
def set_ui_state( request ):
    """
    Set the UI layout data for the user
    """
    def handler( payload ):
        if not payload:
            log.info("SUSPECT - bad ui_state call: %s -> %s", request.user, payload)
            return

        return request.user.tracking.update_state( payload )

    return respond_api_call( request, handler, methods=['POST'] )
