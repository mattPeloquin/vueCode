#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    PayPal express finish page sub-view
"""
import json
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse

from mpframework.common import log
from mpframework.common.logging.utils import pretty_print
from mpextend.product.account.models.apa import APA

from .common import call_paypal_nvp
from .common import money_encode


def flow_end( request ):
    """
    Paypal redirects here if checkout is successful.
    The Payment is NOT completed; need to make PayPal call to finalize,
    and then activate APA if successful.
    """
    from ...models import PayTo
    from ...models import PayUsing

    user = request.user
    sandbox = request.sandbox
    token = request.GET.get('token')
    payer_id = request.GET.get('PayerID')

    # Get details for the transaction (essentially approved at this point)
    response = call_paypal_nvp({
                'METHOD': 'GetExpressCheckoutDetails',
                'TOKEN': token,
                })

    # If something is wrong with the transaction, bail out
    if not response or not response.get('ACK')[0] == 'Success':
        return TemplateResponse( request, 'payment/failed.html', {
                    'reason': 'DETAILS',
                    'response': pretty_print( response ),
                    })

    log.info2("PAY PAYPAL GetExpressCheckoutDetails success %s - %s", user, token )

    # Get custom info sent with transaction; bail if not present
    custom = json.loads( response.get('PAYMENTREQUEST_0_CUSTOM')[0] )
    apa = APA.objects.get( id=custom['apa'] ) if custom else None
    payto = PayTo.objects.get( id=custom['payto'] ) if custom else None
    payusing = PayUsing.objects.get( id=custom['payusing'] ) if custom else None
    if not ( apa and payusing and payto ):
        log.info("SUSPECT PAYPAL no custom: %s, %s -> %s", user, token, custom )
        return TemplateResponse( request, 'payment/failed.html', {} )

    # Get actual price from transaction approval
    amount = money_encode( response.get('AMT')[0] )

    # Call Paypal to finalize
    response = _one_time_payment( payto.service_account,
                payer_id, token, amount )
    success = response and response.get('ACK')[0] == 'Success'

    if not success:
        apa.add_history( _clean_paypal_repsonse( response, "Paypal failure" ) )
        return TemplateResponse( request, 'payment/failed.html', {
                    'reason': 'PAYMENT',
                    'response': pretty_print( response ),
                    })

    log.info("PAY PAYPAL SUCCESS: %s, %s -> %s", user, token, apa )

    # Try to get more details for transaction; if not possible
    # just use the response from checkout payment to activate the APA
    transaction_id = response.get('PAYMENTINFO_0_TRANSACTIONID')
    if transaction_id:
        transaction_details = call_paypal_nvp({
                    'METHOD': 'GetTransactionDetails',
                    'TRANSACTIONID': transaction_id[0],
                    })
        if transaction_details and transaction_details.get('ACK')[0] == 'Success':
            response = transaction_details

    # Activate the APA and store payment details
    apa.save( _user=user,
              _activate=_clean_paypal_repsonse( response, "Paypal payment" )
              )

    # Show success screen or return to portal based on options
    if sandbox.options['payment.show_success']:
        return TemplateResponse( request, 'payment/success.html', {
                    'apa': apa,
                    'amount': amount,
                    'response': pretty_print( response ),
                    })
    else:
        return HttpResponseRedirect( sandbox.portal_url( 'sku', apa.pa.sku ) )


def _one_time_payment( paypal_id, payer_id, token, amount ):
    """
    Execute one-time transaction to spend the money
    """
    log.debug("Paypal finalizing one-time payment: %s -> %s", token, amount)
    return call_paypal_nvp({
                'METHOD': 'DoExpressCheckoutPayment',
                'TOKEN': token,
                'PAYERID': payer_id,
                'PAYMENTREQUEST_0_AMT': amount,
                'PAYMENTREQUEST_0_SELLERPAYPALACCOUNTID': paypal_id,
                })

def _clean_paypal_repsonse( response, summary ):
    rv = "\n{}:\n".format( summary )
    if response:
        for key, value in response.items():
            if not any( s in key for s in _remove ):
                rv += "  {}: {}\n".format( key, value )
    return rv
_remove = [ 'ship', 'gift', 'insurance', 'protection', 'version', 'build' ]
