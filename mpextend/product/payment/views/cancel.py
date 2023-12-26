#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Payment cancel support
"""
from django.http import HttpResponseRedirect

from mpframework.common import log

from ..payment_types import PAYMENT_TYPES


def payment_cancel( request, paytype, **kwargs ):
    """
    Allow sandbox option to not display separate screen on cancel
    """
    pt = PAYMENT_TYPES[ paytype ]
    log.info2("PAYMENT CANCELLED: %s, %s", request.mpipname, pt['name'])
    sandbox = request.sandbox

    response = pt['flow'].cancel.handle_cancel( request )

    if sandbox.options['payment.show_cancel']:
        return response
    else:
        return HttpResponseRedirect( request.sandbox.portal_url() )
