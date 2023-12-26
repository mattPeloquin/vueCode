#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Simple item access
"""

from mpframework.common.api import api_get_id
from mpframework.common.api import respond_api_call

from ..access import get_item_access_data


def item_access( request ):
    """
    User request to access an item - all content access starts here.

    Designed to be overridden in MPF extensions to add
    more functionality around granting access.
    """
    def handler( payload ):
        item_id = api_get_id( payload.pop('id') )
        return get_item_access_data( request, item_id, **payload )

    return respond_api_call( request, handler, methods=['POST'] )
