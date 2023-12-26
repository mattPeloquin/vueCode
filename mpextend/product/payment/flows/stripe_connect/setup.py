#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Stripe sub-view for payment setup
    Supports OAuth linking to existing Stripe account.

    TBD - Add account creation link

    ASSUMES DUCK-TYPING FROM setup.py code
"""
from django import forms
from django.conf import settings
from django.urls import reverse

from mpframework.common import log
from mpframework.common.form import BaseForm
from mpframework.common.form import parsleyfy
from mpframework.common.utils import join_urls
from mpframework.foundation.tenant.models.sandbox import Sandbox

from .common import stripe
from .common import SC


@parsleyfy
class SetupForm( BaseForm ):

    stripe_account = forms.CharField( required=False, disabled=True,
                widget=forms.TextInput(attrs={'size': '64'}) )

def handle_setup_form( request, form, payto ):
    """
    Handle saving of PayTo info
    """
    new_id = form.cleaned_data.get('stripe_account')
    current_id = payto.service_account
    if new_id != current_id:
        payto.service_account = new_id
        payto.payment_config.set( 'connected', False )
        payto.save()
    return {
        'redirect': _get_oauth_url( request ),
        }

def _get_oauth_url( request ):
    redirect = reverse( 'payment_authlink', args=('stripe_connect',) )
    redirect = join_urls( settings.MP_ROOT_URL, redirect, scheme=request.scheme )
    url = '{}?response_type=code&scope=read_write&client_id={}&state={}&redirect_uri={}'.format(
                SC['oauth_url'], SC['client_id'], request.sandbox.id, redirect )
    return url


def handle_authlink( request ):
    """
    Handle response from Stripe for connection
    NO-HOST processing,
    Returns dict with sandbox, payto, and/or error passed from Stripe.
    """
    from ...models import PayTo

    sandbox = request.GET.get('state')
    if sandbox:
        sandbox = Sandbox.objects.get_sandbox_from_id( id=sandbox )
    if not sandbox:
        log.info("PAYMENT ERROR authlink bad sandbox: %s, %s",
                    request.mpipname, sandbox )
        return {
            'error': u"Unable to complete connection.",
            }
    rv = { 'sandbox': sandbox }
    payto = PayTo.objects.get_or_create( 'stripe_connect', sandbox=sandbox )
    if payto:
        rv.update({ 'payto': payto })
        code = request.GET.get('code')
        if code:
            response = stripe.OAuth.token( grant_type='authorization_code', code=code )
            account = response['stripe_user_id']
            payto.service_account = account
            payto.payment_config.set( 'connected', True )
            payto.save()
            log.info("PAYMENT authlink: %s -> %s", payto, response )
        else:
            rv.update({ 'error': request.GET.get( 'error_description',
                        u"There was an error with the request." )})
    else:
        log.info("PAYMENT ERROR authlink no payto: %s, %s",
                    request.mpipname, sandbox )
        rv.update({
            'error': u"Site is not configured for payment.",
            })
    return rv
