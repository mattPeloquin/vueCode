#--- Vueocity Platform, Copyright 2021 Vueocity, LLC
"""
    Request to create a new tenant from onboard session
"""
from django.core.cache import caches
from django.http import HttpResponseRedirect
from django.http import Http404

from mpframework.common import log
from mpframework.common.view import ssl_required

from .. import onboard_session_key
from ..clone import onboard_clone_session
from .signup import cache_session


@ssl_required
def onboard_create( request, token ):
    """
    Handle insecure redirection link for an onboard session,
    typically for system test or from a verification email.
    Creates new provider account and starting sandbox, running under
    context of sandbox hosting the signup for onboard.
    FUTURE - to make email verification work well, need to serve
    a "wait while create" page that then goes to final sandbox.
    """
    from_sandbox = request.sandbox
    try:
        session = caches['session'].get( onboard_session_key( token ) )
        if not session:
            raise Exception("ONBOARD session expired")
        if not from_sandbox.pk == session['from_sandbox']:
            log.warning("SUSPECT ATTACK - ONBOARD session sandbox mismatch")
            raise Http404
        log.info("ONBOARD CREATE: %s -> %s", request.ip,
                    session['sandbox_name'])

        sandbox = onboard_clone_session( from_sandbox, session )
        if sandbox:
            # Update session with ID and send user to new sandbox
            cache_session( session, sandbox )
            return HttpResponseRedirect( sandbox.portal_url() )

        log.warning("ONBOARD sandbox and/or user not created: %s, %s -> %s",
                        request.mpipname, token, sandbox)
    except Exception as e:
        log.exception("ONBOARD create: %s -> %s", token, e)

    # Go back to current sandbox if something went wrong
    return HttpResponseRedirect( from_sandbox.portal_url() )
