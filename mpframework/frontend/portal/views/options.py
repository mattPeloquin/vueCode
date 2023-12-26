#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Special portal endpoint for options that require redirect
"""
import json
from django.http import HttpResponseRedirect

from mpframework.common import log
from mpframework.common.utils.http import append_querystring


def portal_user_options( request, **kwargs ):
    """
    Pass data or options for a user's portal rendering via 'options',
    state to be set, and then redirect back to portal.
    """
    try:
        options = json.loads( kwargs.get('options') )
        log.debug("Setting redirect option: %s", options)
    except json.JSONDecodeError:
        options = {}
    user = request.user
    dirty = False

    # Color2 toggle; depends on current user setting
    if 'color2_toggle' in options:
        user.options['color2'] = not bool( user.options.get('color2') )
        dirty = True

    # Everything below is a staff option
    if user.is_staff:

        # Set workflow to allow staff to easily see dev vs. production
        if 'workflow_level' in options:
            workflow = options.get('workflow_level')
            if user.workflow_level != workflow:
                user.workflow_level = workflow
                dirty = True

        # Toggle Staff user view based on setting
        if 'user_view' in options:
            user_view = options.get('user_view')
            if user.staff_user_view != user_view:
                user.staff_user_view = user_view
                dirty = True

    dirty and user.save()

    # Redirect to referring page adding cache punch through with query string
    url = request.referrer or request.sandbox.portal_url()
    url = append_querystring( url, **{ request.mpinfo.get('tag'): '' } )
    log.info2("Portal option redirect: %s -> %s", options, url)
    return HttpResponseRedirect( url )
