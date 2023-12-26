#--- Vueocity Platform, Copyright 2021 Vueocity, LLC
"""
    Try to log new tenant in
"""
from django.conf import settings
from django.urls import reverse
from django.core.cache import caches
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login

from mpframework.common import log
from mpframework.common.cache import invalidate_key
from mpframework.common.email import send_email_sandbox
from mpframework.common.email import send_email_user
from mpframework.common.view import ssl_required
from mpframework.common.utils.user import session_cookie_name
from mpframework.foundation.tenant.models.sandbox import Sandbox
from mpframework.user.mpuser.models import mpUser

from .. import onboard_session_key


@ssl_required
def onboard_login( request, token ):
    """
    Login a new owner to their sandbox for first time.
    This is called on the CREATING sandbox, which redirects to new.
    """
    from_sandbox = request.sandbox
    try:
        session = caches['session'].get( onboard_session_key( token ) )
        if not session:
            raise Exception("ONBOARD session expired")
        if not from_sandbox.pk == session['from_sandbox']:
            raise Exception("ONBOARD session sandbox mismatch")

        sandbox = Sandbox.objects.get_sandbox_from_id(
                    session['sandbox_id'], session['provider_id'] )
        user = mpUser.objects.get_user_from_email( session['email'], sandbox )

        log.info("ONBOARD LOGIN: %s -> %s, %s", request.ip, sandbox, user)
        if sandbox and user:

            # Only allow one use of session
            invalidate_key( token, 'session' )

            # Open the site customization tool on first entry
            url = sandbox.host_url( reverse('easy_sandbox') )

            # Send message to onboard sandbox's staff email
            send_email_sandbox( from_sandbox, "New Onboard",
                        "{} created '{}' at {}".format( user, sandbox, url ) )

            # Log new owner in and redirect to new sandbox
            auth_user = authenticate( user=user, password=session['password'] )
            if auth_user:
                user = auth_user

                # Figure out UTC from tz offset pass in onboarding form
                for tz in settings.MP_TIME_ZONES:
                    if tz[2] == session['tzoffset']:
                        sandbox.timezone = tz[0]
                        break
                # Save sandbox with user email
                sandbox._email_staff = user.email
                sandbox.save()

                # Log user into new sandbox, taking over this request to
                # prepare redirect response for the new site
                request.sandbox = sandbox
                request.session.flush()
                auth_login( request, user )

                # Send introduction email to new owner
                context = {
                    'root_name': settings.MP_UI_TEXT['root_name'],
                    'user': user,
                    'from_sandbox': from_sandbox,
                    'site': sandbox,
                    'url': sandbox.host_url(),
                    }
                send_email_user( user, 'onboard/welcome_email.html', context )

                # Add session to redirect
                url = url + '?{}={}'.format( session_cookie_name( sandbox ),
                            request.session.session_key )

                log.info("ONBOARD SUCCESSFUL: %s -> %s, %s", sandbox, user, url)
            else:
                log.warning("ONBOARD couldn't login: %s -> %s, %s",
                            request.mpipname, sandbox, user)

            # Send user to to new sandbox; even if something went wrong with login
            return HttpResponseRedirect( url )

        log.warning("ONBOARD sandbox and/or user not created: %s -> %s",
                    request.mpipname, token)
    except Exception as e:
        if settings.MP_DEV_EXCEPTION:
            raise
        log.exception("ONBOARD create: %s -> %s", token, e)

    return HttpResponseRedirect( from_sandbox.portal_url() )
