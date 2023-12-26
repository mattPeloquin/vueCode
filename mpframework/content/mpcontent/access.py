#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Content item protected access wrapper
"""

from mpframework.common import log
from mpframework.common.events import sandbox_event
from mpframework.content.mpcontent.models import BaseItem


def get_item_access_data( request, item, access_fn=None, **kwargs ):
    """
    All requests for accessing protected content are processed here,
    typically from an API call.

    The access_fn is used to determine if the request should be granted
    access. A simple default one is provides with MPF, while
    extensions can add additional functionality.

    Returns URL for access or message to display.
    """
    user = request.user

    # If item is not passed, lookup ID and ensure downcast
    # so access can be specialized
    if not isinstance( item, BaseItem ):
        item = BaseItem.objects.active()\
                    .get( id=item, request=request )\
                    .downcast_model

    log.debug("%s ACCESS item start: %s -> item-%s",
                    request.mptiming, user, item)
    access_data = None

    # Verify the content matches up with user rights
    # Users could not see/click on this content in portal, but
    # make sure a link is not beeing reused/spoofed
    if _has_content_visibility( request, item ):

        # See if user has free access
        free = has_free_access( user, item )

        # Do additional verification or processing
        access_data = access_fn( request, item, free, **kwargs )

    access_data = access_data or {
        'can_access': False,
        }

    # Provide feedback on outcome
    if access_data.get('can_access'):
        request.mpinfo['result'] = 'access_granted'
        if user.is_authenticated:
            sandbox_event( user, 'user_content_access', item,
                    access_data['description'] )
        else:
            sandbox_event( user, 'visitor_content_access', item )
    else:
        request.mpinfo['result'] = 'access_denied'
        if user.is_authenticated:
            sandbox_event( user, 'user_content_denied', item )
        else:
            sandbox_event( user, 'visitor_content_denied', item )

    log.debug("%s ACCESS item complete: %s -> %s", request.mptiming,
                request.mpipname, access_data)
    return access_data


def has_free_access( user, item=None, staff=True ):
    """
    Check the various ways a user would have free access to content.
    Handles both the general case of access to everything (item=None), and
    considering a specific piece of content.
    """
    sandbox = user.sandbox

    # Staff always have access
    rv = user.access_staff_view if staff else None

    # For general case and non-trial items, check free sandbox options
    if not rv and ( not item or not item.sb_options['portal.no_trials'] ):
        rv = sandbox.options['access.free_public']
        if not rv and user.is_ready( sandbox ):
            rv = sandbox.options['access.free_user']

    # Check free settings for item
    if not rv and item:
        # Item marked for public use?
        rv = item.sb_options['access.free_public']
        # Item marked for for free use
        if not rv and user.is_ready( sandbox ):
            rv = item.sb_options['access.free_user']

    log.debug("Access free: %s", rv)
    return rv

def _has_content_visibility( request, item ):
    """
    Return true if workflow and user_level match up reasonably;
    since this only relates to protecting spoofed access links
    (which are protected by time, IP, obfuscation etc.) not
    all cases are handled.
    """
    user = request.user
    workflow_ok = item.workflow in user.workflow_filters
    level = item.sb_options['portal.user_level']
    level_ok = not level
    if not level_ok:
        if user.is_ready( request.sandbox ):
            if level in ['E']:
                level_ok = user.extended_access
            elif level in ['S']:
                level_ok = user.access_staff_view
            else:
                level_ok = True
    rv = workflow_ok and level_ok
    log.debug("Access content visibility: %s", rv)
    return rv

