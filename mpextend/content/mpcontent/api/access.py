#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    User Content API access

    All content access starts here, overriding the default
    mpFramework behavior to add product and tracking.
"""

from mpframework.common import log
from mpframework.common.api import api_get_id
from mpframework.common.api import respond_api_call
from mpframework.content.mpcontent.access import get_item_access_data
from mpextend.product.account.access import content_access_options
from mpextend.user.usercontent.models import ContentUser


def item_access( request ):
    """
    User request to access an item
    Returns either information to access or information to purchase.
    """
    def handler( payload ):
        item_id = api_get_id( payload.pop('id') )

        return get_item_access_data( request, item_id, _access_fn, **payload )

    return respond_api_call( request, handler, methods=['POST'] )

def _access_fn( request, item, free, **kwargs ):
    user = request.user
    rv = { 'can_access': False }

    # Logged in users and staff tie access to usercontent tracking
    if user.is_ready():
        cu = ContentUser.objects.get_contentuser( user )
        if cu:
            rv = cu.item_access_data( request, item, free, **kwargs )

    # Visitors can either have free access, or options shown for purchase
    else:
        if free:
            log.debug("ACCESS without APA: %s, %s", request.mpipname, item )
            rv.update({
                'can_access': True,
                'apa_to_use': 0,
                'description': u"Free access",
                'access_url': item.get_access_url( request, **kwargs ),
                })
        else:
            # Find the options for purchase
            rv.update( content_access_options( item, user ) )

    return rv
