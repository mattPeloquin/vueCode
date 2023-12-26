#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared code for content searching
"""
from django.db.models import Q

from mpframework.common import log
from mpframework.common.cache import cache_rv

from ..models import BaseItem
from ..cache import cache_group_content_sandbox


@cache_rv( keyfn=lambda r, v, limit='':(
            str(v) + limit, cache_group_content_sandbox( r.sandbox ) ) )
def content_search( request, value, limit='' ):
    """
    Optimized and cached search for content item that a user can see that
    matches slug or id - intended for use with external APIs.
    Can search all content, or limit to 'trees' or 'items'.
    """
    query = Q( _slug__iexact=value )
    try:
        query |= Q( id=int(value) )
    except Exception:
        pass
    qs = BaseItem.objects.mpusing('read_replica')\
                .exclude( workflow__in='R' )\
                .filter( user_filter=request.user )\
                .filter( query )
    if limit:
        if limit == 'trees':
            qs = qs.filter( _django_ctype__model='tree' )
        if limit == 'items':
            qs = qs.exclude( _django_ctype__model='tree' )
    rv = qs.first()
    if rv:
        rv = rv.downcast_model
    log.debug("Content search: %s, %s -> %s", request.sandbox, value, rv)
    return rv
