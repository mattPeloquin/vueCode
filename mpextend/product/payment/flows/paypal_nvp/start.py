#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Start Paypal Express transactions
"""
from django.urls import reverse

from mpframework.common import log
from mpframework.common.utils import json_dump

from .common import paypal_nvp
from .common import call_paypal_nvp
from .common import money_encode


def flow_start( request, apa, payto ):
    """
    Returns a URL used to start a paypal NVP transaction by making request
    to the paypal express checkout API.

    Assumes an inactive APA has been created with appropriate details.
    Request is made using ROOT's paypal info, while the transaction
    is setup with the payto ID.
    """
    from ...models import PayUsing

    user = request.user
    assert user and payto and apa

    payusing = PayUsing.objects.get_or_create( payto, apa )

    # Must have a valid paypal ID
    # Don't make assumptions about what paypal id could be because
    # top priority is to make sure money is sent to the right place
    paypal_id = payto.service_account
    if not paypal_id:
        log.info("CONFIG - Sandbox missing paypal ID: %s -> %s",
                    payto, request.mpipname)
        return None, reverse( 'payment_error', args=('paypal_nvp',) )

    log.debug("Paypal process starting: %s - %s", user, request.POST)

    price = money_encode( apa.access_price )
    total = money_encode( apa.access_price + apa.access_tax )

    fields = {
        'METHOD': 'SetExpressCheckout',

        'PAYMENTREQUEST_0_SELLERPAYPALACCOUNTID': paypal_id,

        'PAYMENTREQUEST_0_PAYMENTACTION': 'Sale',
        'PAYMENTREQUEST_0_AMT': total,
        'PAYMENTREQUEST_0_ITEMAMT': price,
        'PAYMENTREQUEST_0_CURRENCYCODE': 'USD',

        'PAYMENTREQUEST_0_CUSTOM': json_dump({
            'apa': apa.pk,
            'payusing': payusing.pk,
            'payto': payto.pk,
            }),
        'PAYMENTREQUEST_0_INVNUM': '{}-{}'.format( user.pk, apa.pk ),

        # Pass line items so PayPal will show total
        'L_PAYMENTREQUEST_0_QTY0': 1,
        'L_PAYMENTREQUEST_0_AMT0': price,
        'L_PAYMENTREQUEST_0_NAME0': apa.pa.name,

        'SOLUTIONTYPE': 'Sole',
        'EMAIL': user.email,

        'NOSHIPPING': 1,
        'ALLOWNOTE': 0,

        'RETURNURL': request.build_absolute_uri(
                    reverse( 'payment_finish', args=('paypal_nvp',) ) ),
        'CANCELURL': request.build_absolute_uri(
                    reverse( 'payment_cancel', args=('paypal_nvp',) ) ),
        }

    if apa.access_tax:
        fields['PAYMENTREQUEST_0_TAXAMT'] = money_encode( apa.access_tax )

    if request.sandbox.logo:
        fields['LOGOIMG'] = request.sandbox.logo.url

    set_express_response = call_paypal_nvp( fields )

    # Bail if transaction wasn't set up
    if not set_express_response or set_express_response.get('ACK')[0] != 'Success':
        log.info("PAY PAYPAL start aborted: %s -> %s, %s", user, price, apa)
        return None, reverse( 'payment_error', args=('paypal_nvp',) )

    token = set_express_response.get('TOKEN')[0]
    log.info("PAY PAYPAL START: %s, %s -> %s, %s", user, token, price, apa)

    return {
        'name': "Paypal",
        'checkout_link': '{}/cgi-bin/webscr?cmd=_express-checkout&token={}'.format(
                paypal_nvp['url_interactive'], token )
        }, None
