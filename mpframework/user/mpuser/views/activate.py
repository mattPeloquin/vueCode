#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Activate new user views
    For now activation is either automatic (not handled here)
    or based on email verification.
"""
import json
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.http import urlsafe_base64_decode
from django.template.response import TemplateResponse
from django.views.decorators.cache import never_cache
from django.contrib.auth.tokens import default_token_generator

from mpframework.common import log
from mpframework.common.utils.login import redirect_login

from ..models import mpUser
from ..utils.activate import activate_user
from ..utils.activate import send_verification_email


@never_cache
def user_verify( request, user_id_b64=None, extra_b64=None, token=None ):
    """
    Implements verification of a clicked email link.

    Checks the token hash to make sure user hasn't changed and
    the token is still valid (uses the Password length setting).

    FUTURE - convert this to use session to store user ID
    """
    assert user_id_b64 is not None and token is not None
    log.debug("New user verify, user: %s, extra: %s, token: %s",
                user_id_b64, extra_b64, token)
    user_id = None
    user = None
    portal_extra = None
    try:
        user_id = urlsafe_base64_decode( user_id_b64 )
        user = mpUser.objects.get( id=user_id )
        portal_extra = urlsafe_base64_decode( extra_b64 )
        log.info2("New user verify: %s -> %s", user, portal_extra)

    except Exception as e:
        log.info("SUSPECT - User email verify error: %s -> %s -> %s",
                    request.mpipname, user_id_b64, e)

    if user:
        if user.activated:
            log.info2("USER - activated, skipping token check: %s, %s -> %s",
                        request.mpipname, user, token)
        else:
            # Token only valid if user hasn't changed since it was issued,
            # and it is in the expiration time frame
            log.debug("Cheking token: %s -> %s", user, token)
            if default_token_generator.check_token( user, token ):
                activate_user( user, request.sandbox, email_verified=True )

        if user.is_authenticated:
            if user.activated:
                # Send to portal if still logged in, or if lost session cookie,
                # make them login again
                return HttpResponseRedirect(
                    request.sandbox.portal_url( **_decode_extra_info( portal_extra ) ))
            else:
                log.info("USER ACTIVATION failed, goto verify: %s -> %s",
                            request.mpipname, user)
                send_verification_email( request )
                return not_verified( request, user=user )
        else:
            return redirect_login( request )

    # Otherwise display error with no user context
    log.info("SUSPECT - USER activation failed, no user: %s -> %s (%s)",
             request.mpipname, user_id, user_id_b64)
    return TemplateResponse( request, 'user/new/activation_error.html', {} )

@never_cache
def not_verified( request, **kwargs ):
    """
    Displayed if user session exists and user is not yet verified.
    (email verification link not clicked)
    """
    ename = kwargs.get('ename')
    evalue = kwargs.get('evalue')
    log.debug2("View not_verified: %s, extra(%s, %s)", request.mpname, ename, evalue)
    user = kwargs.get( 'user', request.user )

    # Only show this screen for users with session cookie (e.g., device change)
    # devices it will be shown again after login
    if not user.is_authenticated:
        return redirect_login( request )

    # Send to portal if they are good to go for email
    if user.is_authenticated and user.email_verified:
        return HttpResponseRedirect( request.sandbox.portal_url( ename, evalue ) )

    # Otherwise display activate screen, with extra info and resend of link
    if request.method == "POST" and 'resend_email' in request.POST:
        log.info("User requested resend of verification email: %s", user)
        send_verification_email( request )
    url = ( reverse('not_verified') if not ename else
            reverse( 'not_verified_extra', kwargs={ 'ename': ename, 'evalue': evalue } )
            )
    return TemplateResponse( request, 'user/login/not_verified.html', {
                                'not_verified_url': url,
                                })

def _decode_extra_info( extra ):
    rv = {}
    try:
        rv = json.loads( extra )
    except Exception:
        log.exception("Decoding extra info: %s", extra)
    return rv
