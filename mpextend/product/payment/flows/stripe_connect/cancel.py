#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Stripe cancel screen
"""
from django.template.response import TemplateResponse

from mpframework.common import log
from mpframework.common.logging.utils import pretty_print


def handle_cancel( request ):
    """
    TBD - Close out canceled Stripe transaction
    """
    session_id = request.GET.get('session_id')
    log.info("PAY STRIPE cancelled: %s, %s", request.mpipname, session_id)
    return TemplateResponse( request, 'payment/cancel.html', {
                'response': pretty_print( {} ),
                })
