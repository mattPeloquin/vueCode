#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Account views
"""
from django.conf import settings
from django.http import HttpResponseRedirect

from mpframework.common import log
from mpextend.product.catalog.models import PA
from mpextend.product.catalog.models import Coupon
from mpextend.product.payment.api import get_payment_start

from ..access import process_new_license
from ..models.account import Account
from ..utils import get_au


# FUTURE - csrf_exempt due to cached form; inject csrf into form
from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def access_select( request ):
    """
    Posted to by access dialog
    Tries to create an APA for the access request (or use existing) while
    handling information posted from the access dialog.

    FUTURE -- turn access request into API request with update of non-cached client items
    """
    user = request.user
    sandbox = request.sandbox
    assert user and sandbox

    POST = request.POST
    pa_id = POST.get('pa_id')
    account_id = POST.get('account_id')
    coupon_code = POST.get('coupon_code')
    postal_code = POST.get('postal_code')
    country = POST.get('country')
    log.info2("ACCESS REQUEST: %s -> pa(%s) acct(%s) coup(%s) addr(%s, %s) -> %s",
              request.mpipname, pa_id, account_id, coupon_code, postal_code,
              country, request.referrer)

    redirect = request.referrer or sandbox.portal_url()
    try:
        # Get the PA the access is granted for
        # Whether access fails or succeeds, try to open portal to that pa
        pa = PA.objects.get_quiet( id=pa_id ) if pa_id else None
        # Lookup any coupon code
        # If no PA passed in, but available from coupon, assign
        coupon = Coupon.objects.coupon_search( sandbox, coupon_code, pa=pa )
        if not pa and coupon and coupon.pa:
            pa = coupon.pa

        # Bail if no PA or put up SKU screen if staff access
        if not pa:
            log.info("Access request BAD PA: %s -> %s", request.mpipname, pa_id)
            return HttpResponseRedirect( redirect )
        if user.access_staff_view:
            log.debug("STAFF ACCESS: %s -> %s", user, pa)
            return HttpResponseRedirect( sandbox.portal_url( 'sku', pa.sku ) )

        # If account wasn't passed or doesn't exist, use user's primary
        account = None
        try:
            account = Account.objects.get( id = account_id )
        except Account.DoesNotExist:
            au = get_au( user )
            if au:
                account = au.primary_account
        if account:
            # If user updated account info in dialog, update it
            _update_account( user, account, postal_code, country )
            # Make sure account can use coupon
            if coupon and not coupon.account_ok( account ):
                coupon = None

        # Go to portal if access, payment if that is an option
        apa = process_new_license( user, pa, account, coupon )
        if apa:
            if apa.is_active( save=True, deep=True ):
                log.debug("User already has access: %s -> %s", user, apa)
                return HttpResponseRedirect( redirect )
            else:
                return HttpResponseRedirect( get_payment_start( request, apa ) )

    except Exception as e:
        log.info("ACCESS REQUEST PROBLEM: %s -> %s, %s, %s, -> %s",
                  request.mpname, pa_id, account_id, coupon_code, e)
        if settings.MP_DEV_EXCEPTION:
            raise

    log.info2("Access request failed, redirecting: %s -> %s", request.mpipname, redirect)
    return HttpResponseRedirect( redirect )

def _update_account( user, account, postal_code, country ):
    """
    If user changed info relating to account info in the access dialog,
    update the DB as needed
    """
    if account.has_admin( user ):
        account_dirty = False

        if postal_code and not account.postal_code == postal_code:
            account.postal_code = postal_code
            account_dirty = True

        if country and not account.country == country:
            account.country = country
            account_dirty = True

        if account_dirty:
            account.save()
