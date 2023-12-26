#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Login front porch

    One view handles all sign-up and sign-in scenarios.
    Derived views can provide login support for specific purposes.

    A major simplifying assumption is that all logins will redirect
    to the portal when successful.
"""
from django.conf import settings
from django.shortcuts import resolve_url
from django.http import HttpResponseRedirect
from django.utils.http import is_safe_url
from django.template.response import TemplateResponse
from django.views.decorators.debug import sensitive_post_parameters
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import REDIRECT_FIELD_NAME

from mpframework.common import log
from mpframework.common.view import ssl_required
from mpframework.common.api import respond_api
from mpframework.common.logging.utils import remove_secrets
from mpframework.common.utils import request_is_authenticated
from mpframework.common.utils.user import session_cookie_name
from mpframework.common.utils.request import get_full_redirect
from mpframework.common.utils.request import QUERYSTRING_PREFIX
from mpframework.common.utils.login import redirect_login
from mpframework.common.utils.http import append_querystring

from ..models import mpUser
from ..forms.create import mpUserCreationForm
from ..forms.authenticate import mpAuthenticationForm
from ..utils.login import login_throttle_check
from ..utils.update import user_request_update
from ..utils.update import user_request_querystrings
from ..utils.activate import send_verification_email
from ..utils.activate import send_welcome_email
from ..utils.activate import activate_user


def login_create( request, **kwargs ):
    kwargs['signup'] = True
    return login( request, **kwargs )

@ssl_required
@sensitive_post_parameters()
def login( request, **kwargs ):
    """
    Adaptation of the Django view login

    Entry point for all login screen views served from server.
    Supports two separate forms for current and new user login.
    All posts return back to this view to allow shared functionality.

    login_extra is used for sku and other redirection to specific
    content or other items in the system.
    """
    template = kwargs.pop( 'template', None )
    template = template or request.skin.login

    # Try login with options, and then once without if problem
    try:
        return _login_process( request, template, **kwargs)
    except Exception:
        log.exception("USER LOGIN %s -> %s", request.ip, request.sandbox)
        if settings.MP_DEV_EXCEPTION:
            raise
        return _login_process( request, template )

def _login_process( request, template, **kwargs ):
    user = request.user
    sandbox = request.sandbox
    login_extra = kwargs.pop( 'login_extra', None )
    login_extra = {} if login_extra is None else login_extra
    log.info3("Login: %s -> %s, %s, %s", request.mpipname,
                template, login_extra, kwargs)

    # Is user already logged in, go straight to the portal
    if request_is_authenticated( request ):
        log.info3("Login already authenticated: %s", request.mpipname)
        user_request_update( request )
        request.is_popup_close = request.is_popup
        return _login( request, _portal_url( sandbox, login_extra ) )

    # For simplicity always setup sign in/up forms, override later as necessary
    # Pass any query string info to create form; don't remove because if user
    # already exists, will be needed to update the user on post
    auth_form = mpAuthenticationForm( sandbox )
    create_form = mpUserCreationForm( sandbox,
                initial=user_request_querystrings( request ) )
    # Is a code needed to continue?
    create_code, login_code = _codes( sandbox, login_extra )

    # Throttling check used for both login attempts and create user
    # (to prevent both password guessing and existing email guessing)
    throttled = login_throttle_check( request )

    # POSTs redirect vs. render after processing
    if request.method == "POST" and not throttled:
        post_str = str( remove_secrets( request.POST ) )[:200]
        log.info("USER LOGIN %s -> %s", request.mpipname, post_str)

        # Login includes validation, failure throttling, and remember me
        if 'login' in request.POST:
            auth_form = mpAuthenticationForm( sandbox, data=request.POST,
                        login_code=login_code )
            if auth_form.is_valid():
                user = auth_form.get_user()
                return _login_user( request, sandbox, user, login_extra )

            log.info2("USER LOGIN INVALID: %s, %s", request.mpipname, post_str)

        # Create new user record and authenticate
        elif 'create_user' in request.POST:
            create_form = mpUserCreationForm( sandbox, request.POST,
                        create_code=create_code )
            if create_form.is_valid():

                # Returns response if user valid, none if email already exists
                response = _login_new_user( request, sandbox,
                            create_form, login_extra )
                if response:
                    return response

                create_form.set_user_exists_error()

            log.info2("USER CREATE INVALID: %s -> %s", request.mpipname, post_str)

    # Handle signin and signup options
    signin = kwargs.pop( 'signin', None )
    signin = request.GET.get( QUERYSTRING_PREFIX + 'signin', signin )
    signup = kwargs.pop( 'signup', None )
    signup = request.GET.get( QUERYSTRING_PREFIX + 'signup', signup )

    # Add form and redirect information to template context
    request.is_no_page_top = True
    extra_context = kwargs.pop( 'extra_context', {} )
    extra_context.update({
            'no_page_top': request.is_no_page_top,
            'auth_form': auth_form,
            'create_form': create_form,
            'throttled': throttled,
            'submit_url': get_full_redirect( request ),
            'has_create_code': bool( create_code ),
            'has_login_code': bool( login_code ),
            'signin': bool( signin ),
            'signup': bool( signup ),
            'login_extra': login_extra,
            })
    return TemplateResponse( request,
                sandbox.get_template( template, user.workflow_dev ),
                extra_context )

def _codes( sandbox, login_extra ):
    """
    Abstract lookup of any sandbox codes.
    """
    create_code = login_extra.get( 'create_code',
            sandbox.policy.get( 'user_create_code', '' ) )
    login_code = login_extra.get( 'login_code', '' )
    return create_code, login_code

def _login_user( request, sandbox, user, login_extra ):
    """
    Handles the login form for the login page
    """
    redirect = request.POST.get( REDIRECT_FIELD_NAME, '' )
    log.debug2("Attempting login and redirect: %s -> %s, %s",
                user, login_extra, redirect)
    assert user.is_active

    # Security check complete; log user in - create/cycle session key if needed
    auth_login( request, user )

    # Implement remember me (default is to use longer time)
    # Setting session to 0 forces logout once browser cookie is gone
    session_length = settings.MP_USER_SESSION_AGE_LONG
    if( sandbox.options['user.force_login'] or
            ( sandbox.options['user.show_remember'] and
                not request.POST.get('remember') ) ):
        session_length = 0
    request.session.set_expiry( session_length )
    log.debug_on() and log.debug2("Session age for %s:  %s",
                user, request.session.get_expiry_age())

    # Perform any request updates
    user_request_update( request )

    # Get any redirection url; if not safe, send to portal
    if not redirect or not is_safe_url( url=redirect, host=request.host ):
        redirect = _portal_url( sandbox, login_extra )

    return _login( request, redirect )

def _login_new_user( request, sandbox, create_form, login_extra ):
    """
    Handles the create new user form for the login page
    After processing users either see screen to look for init email,
    go straight to the portal if activated, or back to login if errors.
    """
    data = create_form.cleaned_data
    email = data.pop('email')
    password = data.pop('password1')

    # Mistaking create for login is a common mistake.
    # Instead of forcing user to use correct form, check if the user exists
    # and if they authenticate with the password, treat as login
    user = mpUser.objects.get_user_from_email( email, sandbox )
    if user:
        user = authenticate( user=user, password=password )
        if user and user.activated:
            log.info2("USER - Existing create login: %s", request.mpipname)
            return _login_user( request, sandbox, user, login_extra )
        else:
            log.info2("USER - Existing create, login fail: %s", request.mpipname)
            return redirect_login( request )

    # No user exists, create new user record
    log.info("USER CREATE: %s -> %s", request.mpipname, email)
    user = mpUser.objects.create_obj( sandbox=sandbox, email=email,
                password=password, create_info=login_extra, **data )
    if not user:
        raise Exception("SUSPECT - Could not create user")

    # If no authenticate with password just saved, something weird happened
    user = authenticate( user=user, password=password )
    if not user:
        raise Exception("SUSPECT - New user authentication failed")

    if sandbox.policy['verify_new_users']:
        log.info("USER - verification email: %s -> %s", user, login_extra)
        # NOTE -- this uses token generation from Django password reset, so includes
        # the last login and password info from user, so need to do an initial login
        # and then can't do a login again without the token becoming invalid
        auth_login( request, user )
        send_verification_email( request, user, **_portal_extra( login_extra ) )
    else:
        log.info("USER - activating immediately: %s", user)
        activate_user( user, request.sandbox )
        auth_login( request, user )
        send_welcome_email( request, user )

    # Pull querystrings from request URL since any changes already saved with form
    user_request_querystrings( request, remove=True )

    return _login( request, _portal_url( sandbox, login_extra ) )

def _portal_url( sandbox, login_extra ):
    return resolve_url( sandbox.portal_url( **_portal_extra( login_extra ) ) )

def _portal_extra( login_extra ):
    return login_extra.get( 'portal_extra', {} )

def _login( request, url, **qs_adds ):
    """
    All logins (new and existing users) flow through here.
    """
    if request.is_api:
        data = {
            'redirect_url': url,
            }
        return respond_api( data )

    sandbox = request.sandbox

    # If redirect crosses domain, send to session/url redirect if sandbox allows
    host = sandbox.main_host.host_name if sandbox.main_host else ''
    if host != request.host:
        log.info3("Sandbox/request host fixup: %s -> %s, %s",
                    request.mpipname, host, request.host)
        qs_adds[ session_cookie_name( sandbox ) ] = request.session.session_key
    else:
        log.debug2("Sandbox and request hosts match for: %s", url)

    # Add querystring to indicate this came from popup login
    if request.is_popup:
        qs_adds[ QUERYSTRING_PREFIX + 'popup_close' ] = 1

    url = append_querystring( url, **qs_adds )
    return HttpResponseRedirect( url )
