#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Page that hosts the start of a payment flow.
"""
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse

from mpframework.common import log

from ..payment_types import PAYMENT_TYPES
from ..payment_start import get_payment_options


def payment_start( request, apa_id, paytype=None ):
    """
    This view starts the payment process. When more than one PayTo is
    available, page will be visited twice, first to select, and
    then to start the payment.
    """
    pay_start = None
    paytos = []
    pay_options = []
    paytype = paytype if paytype in PAYMENT_TYPES else None

    # Get active payto options
    apa, all_paytos = get_payment_options( request, apa_id )

    for pt in all_paytos:
        if pt.is_active and ( not paytype or pt.payment_type == paytype ):
            paytos.append( pt )
    log.debug("Payment start paytos: %s", paytos)

    if not paytos:
        return TemplateResponse( request, 'payment/failed.html', {
                    'reason': 'CONFIG',
                    })

    # If one payto fits criteria, use it to start payment
    payto = paytos[0] if len(paytos) == 1 else None
    if payto:
        log.info("PAYMENT start: %s, %s %s", request.mpipname, apa, payto)
        start_fn = PAYMENT_TYPES[ payto.payment_type ]['flow'].start.flow_start
        pay_start, error_link = start_fn( request, apa, payto )

        if error_link:
            return HttpResponseRedirect( error_link )

    # Otherwise display options
    else:
        for pt in paytos:
            option = pt.dict
            option['link'] = reverse( 'payment_start', args=(
                        apa.pk, pt.payment_type ))
            pay_options.append( option )

    return TemplateResponse( request, 'payment/start.html', {
                'apa': apa,
                'pay_start': pay_start,
                'pay_options': pay_options,
                })
