#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Provide payment options to frontend
"""

from mpframework.common.api import respond_api_call

from ..payment_start import get_payment_options


def api_payment_options( request, apa_id ):
    def handler( _get ):
        apa, options = get_payment_options( request, apa_id )
        return apa.dict, [ p.dict for p in options ]
    return respond_api_call( request, handler, methods=['GET'] )
