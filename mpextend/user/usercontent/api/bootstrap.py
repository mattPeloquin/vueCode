#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    User content API Bootstrap

    Methods here are registered as part of the bootstrap process

    Root information is sent before items as an optimization for getting and
    user-specific information in top collections that affect portal rendering.

    FUTURE - could provide some visitor support for item usage
"""
from django.conf import settings

from mpframework.common import log

from ..models import ContentUser


def user_tops( request, **kwargs ):
    return _user_content( request, True, **kwargs )

def user_items( request, **kwargs ):
    return _user_content( request, False, **kwargs )

def _user_content( request, tops_only, **kwargs ):
    """
    Shared code for returning content metadata specific to the user

    It is possible for this to be called for visitors or users without
    a ContentUser (e.g., user hasn't been active yet).

    Will return an empty list if items can't be identified for the user,
    will try to create a ContentUser record if it doesn't exist.

    FUTURE OPTIMIZATION - Cache user item per-item dict and update cache in place
    """
    rv = []
    user = request.user
    cu = ContentUser.objects.get_contentuser( user )
    if not cu:
        log.debug("No content user for user content: %s", user)
        return rv
    if log.debug_on():
        log.debug2("UserContent loading items: %s", user)
        rt = request.mptiming
        log.timing("%s %s START USER ITEMS: %s, tops: %s", rt.pk, rt, user, tops_only)
        rt.mark()

    # Get content user item info
    useritems = cu.my_items
    if tops_only:
        useritems = useritems.filter( top_tree_id=None )
    useritems = useritems\
                .values( 'item_id', 'progress', 'apa_id',
                            'last_used', 'seconds_used' )\
                .filter( **kwargs )

    # Add info if any values are non-default
    for ui in useritems.iterator():
        try:
            values = {}
            if ui['progress']:
                values['status'] = ui['progress']
                values['last_used'] = ui['last_used']
                values['min_used'] = ui['seconds_used'] // 60
            if ui['apa_id']:
                values['apa'] = ui['apa_id']
            if values:
                values['id'] = ui['item_id']
                rv.append( values )
        except KeyError:
            if settings.MP_TESTING:
                raise

    log.debug_on() and log.debug("%s FINISHED USER ITEMS(%s) %s: %s items ", rt.pk,
                                                    rt.log_recent(), rt, len(rv) )
    return rv
