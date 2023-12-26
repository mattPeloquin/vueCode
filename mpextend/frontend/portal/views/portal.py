#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Portal endpoints

    Unlike portal tool modifications, any modifications
    through these endpoints are template cached for production use.
"""
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import ensure_csrf_cookie

from mpframework.common import log
from mpframework.common.utils.strings import bool_convert
from mpframework.common.utils.request import QUERYSTRING_PREFIX
from mpframework.frontend.portal.views import sandbox_portal
from mpextend.product.payment.api import get_payment_options
from mpextend.product.payment.api import get_payment_start

from ._extra import process_extra


@ensure_csrf_cookie
def sandbox_portal_extend( request, **kwargs ):
    """
    Loads the portal (either sandbox default or customized)
    Unlike portal tool modification, these customizations
    are specific endpoints that are cached and used in production.
    """
    context = kwargs.get( 'context', {} )

    # If there is an inactive APA and options are set to go to payment,
    # save the tree ID related to the product and redirect to start payment
    apa = context.get('portal_apa')
    if apa and not apa.is_active( deep=True ):
        direct_payment = _try_direct_payment( request, apa )
        if direct_payment:
            return HttpResponseRedirect( direct_payment )

    return sandbox_portal( request, **kwargs )

"""
    Portals can load from extra URLs that define different behaviors.
    These could be accessed directly, but are typically redirected
    from the EasyLink user login urls.
"""

def portal_extra( request, **kwargs ):
    process_extra( request, kwargs )
    return sandbox_portal_extend( request, **kwargs )


def _try_direct_payment( request, apa ):
    """
    Purchase request to send direct into payment screen; only honored if
    the APA is setup for it and there is only 1 payment option
    """
    if not bool_convert( request.GET.get(
                QUERYSTRING_PREFIX + 'direct_payment',
                apa.rules['no_prompt'] )):
        return

    # Check the payment options
    _apa, options = get_payment_options( request, apa )

    # Save return state and redirect to payment if options available
    if options:
        log.info2("Navigating direct to payment: %s", apa)
        return get_payment_start( request, apa )
