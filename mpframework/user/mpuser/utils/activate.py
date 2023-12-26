#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    User activation utilities
"""
import json
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site

from mpframework.common import log
from mpframework.common.utils import now
from mpframework.common.email import send_email_user

from ..signals import mpuser_activated


def activate_user( user, sandbox, email_verified=False ):
    log.info("USER ACTIVATING: %s -> %s, v=%s", sandbox, user, email_verified)

    user.email_verified = email_verified
    user.init_activation = "{} - {} - {}".format( user.email, now(), sandbox.name )
    user.save()

    mpuser_activated.send( sender=sandbox.pk, user=user )

def send_welcome_email( request, user ):
    sandbox = request.sandbox
    try:
        if sandbox.options['user.no_welcome_email']:
            return
        log.debug("Sending user welcome email: %s -> %s", sandbox, user )
        send_email_user( user, 'user/new/first_email.html', {
                'user': user,
                'site': sandbox,
                })
    except Exception:
        log.exception("Error sending welcome email: %s -> %s", sandbox, user)

def send_verification_email( request, user=None, **kwargs ):
    sandbox = request.sandbox
    user = user if user else request.user
    log.debug("Sending new user email verification: %s -> %s, %s)",
                sandbox, user, kwargs)

    user_id = urlsafe_base64_encode( force_bytes( user.pk ) )
    token = default_token_generator.make_token( user )
    log.info2("User verify: %s( %s ), token: %s", user, user_id, token)

    extra_encode = urlsafe_base64_encode( _encode_extra_info( kwargs ) )

    # Use site/domain from request instead of user sandbox to better
    # support testing scenarios - so email link will come from URL being used with sandbox
    current_site = get_current_site( request )

    send_email_user( user, 'user/new/first_email.html', {
            'email_user_activate': True,
            'user': user,
            'site': sandbox,
            'domain': current_site.domain,
            'user_id': user_id,
            'extra': extra_encode,
            'token': token,
            'scheme': request.scheme,
            })

def _encode_extra_info( values ):
    rv = '{}'
    try:
        rv = json.dumps( values )
    except Exception:
        log.exception("Encoding extra info: %s", values )
    return force_bytes( rv )
