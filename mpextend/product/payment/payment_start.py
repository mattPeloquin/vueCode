#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Start a payment process
"""
from django.urls import reverse

from mpframework.common import log
from mpextend.product.account.models import APA

from .payment_types import PAYMENT_TYPES
from .models import PayTo


def get_payment_options( request, apa ):
    """
    Determine client payment options available for the APA.
    Returns apa and the options, as optimization when APA is
    looked up from ID.
    """
    if not isinstance( apa, APA ):
        apa = APA.objects.get_from_id( request.sandbox, apa )
    if not apa:
        return None, []
    return apa, PayTo.objects.get_paytos( apa )


def get_payment_start( request, apa, paytype=None ):
    """
    Returns URL for starting payment page if valid options exist.
    """
    log.debug("Start payment %s: %s, %s", request.mpipname, apa, paytype)
    sandbox = request.sandbox
    if not apa:
        return sandbox.portal_url()

    apa, paytos = get_payment_options( request, apa )
    if not paytos:
        return reverse( 'payment_error', args=( paytype ,) )

    return reverse( 'payment_start', args=( apa.pk, paytype ))
