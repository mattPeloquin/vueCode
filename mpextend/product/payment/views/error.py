#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Payment error page
    Only used when an error needs to redirect to a landing page.
"""
from django.template.response import TemplateResponse

from mpframework.common import log

from ..payment_types import PAYMENT_TYPES


def payment_error( request, paytype, **kwargs ):
    pt = PAYMENT_TYPES[ paytype ]
    log.info("PAYMENT ERROR: %s, %s", request.mpipname, pt['name'])

    response = None
    error_handler = getattr( pt['flow'], 'error', None )
    if error_handler:
        response = error_handler.flow_error( request )

    if response:
        return response
    else:
        return TemplateResponse( request, 'payment/failed.html', {
                    'reason': 'PAYMENT',
                    })
