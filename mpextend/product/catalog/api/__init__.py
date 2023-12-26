#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Catalog API Views
"""

from mpframework.common import log
from mpframework.common.utils import json_dump
from mpframework.common.api import respond_api_call

from ..models.pa import PA
from ..models.coupon import Coupon


def pa_info( request, pa_slug=None ):
    """
    Returns information about the requested product agreement
    """
    def handler( _get ):
        if pa_slug:
            sandbox = request.sandbox
            log.debug("API - Getting PA info: %s -> %s", sandbox, pa_slug)
            pa = PA.objects.pa_search( sandbox, pa_slug )
            return {
                'pa_info': pa.json(),
                }
    return respond_api_call( request, handler, methods=['GET'] )


def coupon_info( request, coupon_slug=None ):
    """
    Returns coupon information
    """
    sandbox = request.sandbox

    def handler( payload ):
        """
        Request for coupon info may include a PA id; this value is not used for
        coupon lookup, but is passed back to preserve state for client
        """
        if coupon_slug:
            pa_id = payload.get('pa_id')
            log.debug("API - Getting Coupon info: %s -> %s, %s)", coupon_slug, pa_id, sandbox)
            rv = { 'original': json_dump({
                        'pa_id': pa_id,
                        'code': coupon_slug,
                        })
                    }
            coupon = Coupon.objects.coupon_search( sandbox, coupon_slug )
            if coupon:
                rv.update({
                    'coupon': coupon.json(),
                    })
            log.debug2("API coupon info: %s", rv)
            return rv

    return respond_api_call( request, handler, methods=['GET'] )
