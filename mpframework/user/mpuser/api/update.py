#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Support user modifications of settings outside forms
"""
from mpframework.common import log
from mpframework.common.delivery import *
from mpframework.common.api import respond_api_call
from mpframework.common.view import login_required


_TOGGLE_ROTATION = [
        DELIVERY_PARENT,
        DELIVERY_COMP_COOKIE,
        DELIVERY_COMP_QUERY,
        ]

@login_required
def set_delivery_mode( request ):
    """
    Set the delivery mode for the user
    """
    def handler( payload ):
        user = request.user
        sandbox = request.sandbox
        mode = payload.get('delivery_mode')

        if sandbox.options['access.no_user_change'] or not _mode_valid( mode ):
            log.info("SUSPECT - ignoring delivery mode change: %s", user)
            return

        if mode == 'toggle':
            log.debug("Toggling user mode: %s -> %s", user, user._delivery_mode )
            try:
                current = _TOGGLE_ROTATION.index( user._delivery_mode )
                next = current + 1 if current < len( _TOGGLE_ROTATION ) else 0
                mode = _TOGGLE_ROTATION[ next ]
            except ValueError:
                mode = DELIVERY_PARENT

        log.info("USER MODE CHANGE: %s -> %s", request.mpipname, mode)
        user._delivery_mode = mode
        user.save()
        return user.delivery_mode()

    return respond_api_call( request, handler, methods=['POST'] )

def _mode_valid( mode ):
    return mode in [ 'toggle' ] + _TOGGLE_ROTATION
