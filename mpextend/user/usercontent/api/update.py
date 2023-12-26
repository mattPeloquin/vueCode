#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    User content update API views
"""

from mpframework.common import log
from mpframework.common.view import staff_required
from mpframework.common.api import respond_api_call

from ..models import UserItem


@staff_required
def update_version( request ):
    """
    For the item id given in post, force user content to update to
    the latest version for that item
    """
    def handler( payload ):
        item_id = payload.get('item_id')
        log.debug("API update_version: %s -> %s", request.user, item_id)

        cu_items = UserItem.objects.filter( sandbox=request.sandbox, item_id=item_id )
        for cui in cu_items.iterator():
            cui.update_version()
            cui.save()

        return { 'users_updated': cu_items.count() }

    return respond_api_call( request, handler, methods=['POST'] )

