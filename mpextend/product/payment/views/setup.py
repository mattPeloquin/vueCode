#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Page for adding and updating PayTo
"""
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse

from mpframework.common.view import staff_required
from mpframework.common.utils.http import append_querystring

from ..payment_types import PAYMENT_TYPES
from ..api.setup import get_payment_setups


@staff_required
def payment_setup( request, paytype=None ):
    """
    Display all configured and available PayTo options on one screen.
    paytype selects one to select on load.
    """
    setups = get_payment_setups( request )
    setup_forms = {}
    setup_types = []
    start_type = None
    for pt in PAYMENT_TYPES.values():
        existing = setups.get( pt['service'], {} )
        prefix = u"Edit" if existing else u"Add"
        setup_types.append({
            'id': pt['service'],
            'text': "{} {} payment".format( prefix, pt['name'] ),
            })
        if paytype and paytype == pt['service']:
            start_type = setup_types[-1]

        # Initialize all forms to current state (most start hidden)
        current_values = existing.get( 'config', {} )
        current_values.update({
            pt['flow'].common.ACCOUNT_NAME: existing.get('service_account'),
            })
        setup_forms[ pt['service'] ] = pt['flow'].setup.SetupForm(
                    initial=current_values )

    request.is_page_staff = True
    return TemplateResponse( request, 'payment/setup.html', {
                'setups': setups,
                'types': setup_types,
                'forms': setup_forms,
                'start': start_type,
                })

def payment_authlink( request, paytype ):
    """
    Delegate callbacks from payment connect to appropriate flow
    NO-HOST REQUEST - sandbox must be passed in URL, need to
    REDIRECT to the setup page to point user's browser back
    at the sandbox.
    """
    setup = PAYMENT_TYPES[ paytype ]['flow'].setup

    outcome = setup.handle_authlink( request )
    sandbox = outcome.get('sandbox')
    if sandbox:
        redirect = '{}{}'.format( sandbox.main_host_ssl,
                    reverse( 'payment_setup', args=(paytype,) ) )
        error = outcome.get('sandbox')
        if error:
            append_querystring( redirect, error=error )

        return HttpResponseRedirect( redirect )
