#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Proxy views
"""
from django.views.decorators.csrf import csrf_exempt

from mpframework.common import log
from mpframework.common.view import login_required
from mpframework.content.mpcontent.models import BaseItem


@csrf_exempt
@login_required
def protected_proxy_cache( request, cache_id ):
    """
    URL for proxy sessions whose path DOES NOT INCLUDE PROXY SESSION
    (so isn't actually protected).
    Used for static files requested via URLs from dynamic proxy pages,
    and is only called when a proxy is configured to redirect here.

    Unlike protected sessions, this does require a user to be logged in,
    so will not work in compatibility situations where request
    authentication is stripped.
    """

    item = BaseItem.objects.get( id=cache_id, sandbox=request.sandbox )
    proxy_item = item.downcast_model
    log.debug("PROXY cache request: %s -> %s", request.uri, proxy_item)

    return proxy_item.get_proxy_response( request )
