#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Portal content access API
"""

from mpframework.common import log
from mpframework.common.api import api_get_id
from mpframework.common.api import respond_api_call
from mpframework.content.mpcontent.models import BaseItem

from .access import get_apa_dicts
from .access import content_access_options


def access_options( request ):
    """
    Provide purchase options.
    This is always publicly available to provide options for UI.
    """
    def handler( payload ):
        user = request.user
        item = api_get_id( payload.get('id'), required=False )
        if item:
            item = BaseItem.objects.active()\
                        .get_quiet( id=item, request=request )
        log.debug("Access options: %s -> item-%s", user, item)
        return content_access_options( item, user )

    return respond_api_call( request, handler, methods=['POST'] )


def access_apas( request ):
    """
    Return set of APAs currently active for this user.
    """
    def handler( _get ):
        return get_apa_dicts( request.user )

    return respond_api_call( request, handler, methods=['GET'] )
