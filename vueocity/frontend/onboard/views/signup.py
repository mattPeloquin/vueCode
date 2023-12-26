#--- Vueocity Platform, Copyright 2021 Vueocity, LLC
"""
    View support for signing up new provider
    Uses a form defined in template

    FUTURE SECURE - Support email for onboard verification
    FUTURE SECURE - Add throttling to signups
"""
from django import forms
from django.conf import settings
from django.core.cache import caches
from django.urls import reverse
from django.http import Http404
from django.http import HttpResponseRedirect
from django.views.decorators.debug import sensitive_post_parameters

from mpframework.common import log
from mpframework.common.api import respond_api_call
from mpframework.common.view import ssl_required
from mpframework.common.utils import get_random_key
from mpframework.common.ip_throttle import boost_ip
from mpframework.foundation.tenant.models.sandbox import Sandbox
from mpframework.user.mpuser.models import mpUser
from mpframework.user.mpuser.forms.create import CreateUserBaseForm
from mpextend.common.request_info import is_threat

from .. import onboard_session_key
from ..clone import onboard_clone_session


ONBOARD_EXPIRATION = 3600


class OnboardForm( CreateUserBaseForm ):
    """
    Support creation of new provider users, while sharing some code
    with the main sandbox user creation
    """
    error_messages = dict( CreateUserBaseForm.error_messages, **{
        'email': u"The provided email is not valid",
        'subdomain': u"The requested domain name is invalid or already in use",
        })

    # Name and domain name for provider and first sandbox
    sandbox_name = forms.CharField()
    subdomain = forms.CharField()
    onboard_role = forms.CharField()
    tzoffset = forms.CharField( required=False )
    code1 = forms.CharField( required=False )

    def clean_subdomain( self ):
        subdomain = self.cleaned_data.get('subdomain')
        subdomain = Sandbox.objects.subdomain_ok( subdomain )
        if not subdomain:
            raise forms.ValidationError( self.error_messages.get('subdomain') )
        return subdomain.lower()

    def clean_email( self ):
        email = self.cleaned_data.get('email')
        # Make sure the email is not in use as root account
        users = mpUser.objects.filter( _provider=settings.MP_ROOT['PROVIDER_ID'],
                                       email__iexact=email )
        if users:
            raise forms.ValidationError( self.error_messages.get('email') )
        return email


# TBD - csrf_exempt due to cached form; inject csrf into form
from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
@ssl_required
@sensitive_post_parameters()
def onboard_signup( request ):
    """
    Accepts POSTs from a sandbox page that is configured for onboarding.
    Creates a temporary onboard session for copying the template sandbox, which
    can be activated immediately or via a link sent in verification email.
    """
    try:
        boost_ip( request.ip )
        if request.sandbox.pk not in settings.MP_ROOT_ONBOARD_SETUP:
            log.info2("SUSPECT - onboard bad sandbox: %s -> %s",
                    request.sandbox.subdomain, request.mpipname)
            raise Http404
        if is_threat( request.ip ):
            log.info2("SUSPECT - onboard threat IP: %s", request.mpipname)
            raise Http404

        session = _create_onboard_session( request )
        log.info_mail("ONBOARD signup: %s %s %s (%s)", session['subdomain'],
                session['email'], session['onboard_role'], session['token'] )

        # For ajax posts (main path), start copy process and return
        if request.is_api:
            new_sandbox = onboard_clone_session( request.sandbox, session )
            if new_sandbox:
                cache_session( session, new_sandbox )
                return respond_api_call( request, {
                            'token': session['token'],
                            'sandbox': new_sandbox.pk,
                            }, methods=['POST'] )
        # For form post (testing), redirect to page used for email verify
        else:
            cache_session( session )
            return HttpResponseRedirect( reverse(
                        'onboard_create', args=[ session['token'] ]) )

        log.warning("ONBOARD failed: %s -> %s", request.mpipname, session)
    except Exception as e:
        log.info2("SUSPECT ONBOARD: %s %s %s -> %s", request.mpipname,
                    request.method, request.uri, e)
    if request.is_api:
        return respond_api_call( request, {} )
    else:
        return HttpResponseRedirect( request.sandbox.portal_url() )

def cache_session( session, sandbox=None ):
    """
    Place the onboard session into the cache; add sandbox info
    if it has been created
    """
    if sandbox:
        session['sandbox_id'] = sandbox.pk
        session['provider_id'] = sandbox._provider_id

    caches['session'].set( onboard_session_key( session['token'] ),
                            session, ONBOARD_EXPIRATION )

def _create_onboard_session( request ):
    """
    If request is ok setup cached "create session" to track information on
    the new provider request past the email validation.
    """
    form = OnboardForm( data=request.POST )
    if not form.is_valid():
        raise Exception( "Invalid form: %s -> %s" % ( form.errors,
                    str(form.data)[:200] ) )
    if 'code1' not in form.data or form.data['code1']:
        raise Exception( "Honey pot: %s" % str(form.data)[:200] )

    data = form.cleaned_data
    return {
        'token': get_random_key( prefix='ob' ),
        'from_sandbox': request.sandbox.pk,
        'sandbox_name': data['sandbox_name'],
        'subdomain': data['subdomain'],
        'onboard_role': data['onboard_role'],
        'email': data['email'],
        'password': data['password1'],
        'tzoffset': data['tzoffset'],
        }
