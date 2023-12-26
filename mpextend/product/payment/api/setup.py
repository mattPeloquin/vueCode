#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Support setting up PayTo relationships
"""

from mpframework.common import log
from mpframework.common.api import respond_api_call
from mpframework.common.view import staff_required

from ..models import PayTo
from ..payment_types import PAYMENT_TYPES


@staff_required
def payment_setups( request ):
    def handler( _get ):
        return get_payment_setups( request )
    return respond_api_call( request, handler, methods=['GET'] )

def get_payment_setups( request ):
    """
    Return dict of setup PayTo payment integrations
    """
    rv = {}
    for payto in PayTo.objects.filter( sandbox=request.sandbox ).iterator():
        rv[ payto.payment_type ] = payto.dict
    return rv


@staff_required
def payment_setup( request, paytype ):
    """
    Delegate update PayTo posts to appropriate service handler,
    usually as ajax submit from UI screen.
    """
    def handler( payload ):

        setup = PAYMENT_TYPES[ paytype ]['flow'].setup
        form = setup.SetupForm( payload )
        log.debug("Payment setup form: %s, %s", form.errors, form.cleaned_data)
        if form.is_valid():
            payto = PayTo.objects.get_or_create( paytype, sandbox=request.sandbox )
            log.info2("Payment setup: %s", payto)
            return setup.handle_setup_form( request, form, payto )

    return respond_api_call( request, handler, methods=['POST'] )
