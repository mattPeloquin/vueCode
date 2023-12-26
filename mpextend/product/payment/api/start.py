#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Start a payment process
"""

from mpframework.common.api import respond_api_call

from ..payment_types import PAYMENT_TYPES
from ..payment_start import get_payment_start


def api_payment_start( request, apa_id, paytype=None ):
    if not paytype:
        paytype = list( PAYMENT_TYPES )[0]
    def handler( _get ):
        return get_payment_start( request, apa_id, paytype )
    return respond_api_call( request, handler, methods=['GET'] )
