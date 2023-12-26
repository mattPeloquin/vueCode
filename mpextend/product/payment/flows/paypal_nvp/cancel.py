#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    PayPal express cancel screen
"""
import json
from django.template.response import TemplateResponse

from mpframework.common import log
from mpframework.common.utils import now
from mpframework.common.logging.utils import pretty_print
from mpextend.product.account.models.apa import APA

from .common import call_paypal_nvp


def handle_cancel( request ):
    """
    Subview PayPal and MPF code redirects to if the payment does not complete.
    Record any failure codes in APA for tracking
    """
    token = request.GET.get('token')
    log.info("PAYPAL cancelled: %s, %s", request.mpipname, token)
    paypal_info = ""
    if token:
        # Get any explanation from Paypal
        get_express_response = call_paypal_nvp({
                    'METHOD': 'GetExpressCheckoutDetails',
                    'TOKEN': token,
                    })

        if get_express_response:
            paypal_info = pretty_print( get_express_response )

            # Try to place the info in the APA
            custom = json.loads( get_express_response.get('PAYMENTREQUEST_0_CUSTOM')[0] )
            apa = APA.objects.get( id=custom['apa'] ) if custom else None
            if apa:
                log.debug("Updating APA with cancel info: %s", apa)
                info = u"\nUSER CANCELLED PAYPAL ({}) {}:\n{}\n".format(
                            now(), request.user, paypal_info )
                apa.add_history( info )

    return TemplateResponse( request, 'payment/cancel.html', {
                'response': pretty_print( paypal_info ),
                })
