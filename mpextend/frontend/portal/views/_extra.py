#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Handle processing of portal extra values
"""
from urllib.parse import unquote
from django.conf import settings
from django.core.cache import caches

from mpframework.common import log
from mpframework.common.utils import safe_int
from mpframework.common.cache import invalidate_key
from mpframework.content.mpcontent.utils import content_search
from mpextend.product.catalog.models import PA
from mpextend.product.catalog.models import Coupon
from mpextend.product.account.models import APA
from mpextend.product.account.models import GroupAccount
from mpextend.product.account.access import process_new_license
from mpextend.product.account.utils import get_au
from mpextend.user.plan.models import UserPlan


_cache = caches['session']


def process_extra( request, kwargs ):
    """
    Parse out extra information passed to portal request and update the
    kwargs passed along to sandbox portal.
    """
    ename = kwargs.pop( 'ename', '' )
    evalue = kwargs.pop( 'evalue', '' )
    if not ( evalue and ename ):
        log.debug2("No extra portal values: %s, %s", request.mpname, ename, evalue)
        return

    context = kwargs.get( 'context', {} )
    try:
        sandbox = request.sandbox
        user = request.user
        catalog = None
        content = None

        # A requested portal path trumps other options
        if ename == 'path':
            context['nav_to_path'] = evalue
            return

        # Account requests attach user to GA and APA if valid
        if ename == 'account':
            _attach_user_to_account( request, evalue )

        # SKU requests determine specific content and price
        elif ename == 'sku':
            catalog = _sku_process( request, evalue, context )

        # Coupon requests are either tied to a PA or general - the pathway for coupon
        # links varies depending on that relationship and if they are free
        elif ename == 'coupon':
            catalog = _coupon_process( request, evalue, context )

        # Access is based on SKU and optional SKU-specific coupon
        elif ename == 'access':
            sku, coupon = unquote( evalue ).split(',')
            catalog = _sku_process( request, sku, context )
            if coupon:
                _coupon_process( request, coupon, context )

        # Content requests direct to content and put up purchase dialog if no access
        elif ename == 'content':
            content = content_search( request, evalue )
            log.info2("PORTAL Content: %s -> %s", request.mpipname, content)

        # If a catalog item was provided, add content to plan and get content
        # Content will be navigated to unless tag matches all content
        if catalog:
            if not catalog.includes_all:
                content = catalog.get_top_collections()
                if user.is_ready() and not sandbox.options['user.no_add_plan']:
                    log.debug("Adding to user plan: %s -> %s", user, catalog)
                    plan = UserPlan.objects.get_or_create( user )
                    plan.add_collections( content )

        # If request points to content set start state navigation to go there
        _content_nav_start( request, content, context )

        kwargs['context'] = context

    except Exception as e:
        if settings.MP_DEV_EXCEPTION:
            raise
        log.info2("No extra match: %s -> %s, %s -> %s", request.mpipname, ename, evalue, e)
        if settings.MP_TESTING:
            raise

def _sku_process( request, evalue, context ):
    rv = None
    pa = PA.objects.pa_search( request.sandbox, evalue )
    log.info2("PORTAL SKU: %s, %s -> %s", request.mpipname, evalue, pa)
    if pa:
        if pa.available:
            _check_user_pa( request, pa, context )
            rv = pa
        else:
            log.info2("SKU unavailable: %s -> %s", request.mpipname, pa)
    else:
        log.info2("SKU not found: %s -> %s", request.mpipname, evalue)
    return rv

def _coupon_process( request, evalue, context ):
    rv = None
    coupon = Coupon.objects.coupon_search( request.sandbox, evalue )
    log.info2("PORTAL Coupon: %s, %s -> %s", request.mpipname, evalue, coupon)
    if coupon:
        context.update({ 'portal_coupon': coupon })
        if coupon.pa and coupon.pa.available:
            _check_user_pa( request, coupon.pa, context, coupon )
            rv = coupon
        else:
            # Select non-free PAs visible to all to show in access dialog
            pas_to_show = PA.objects.get_purchase_pas( request.sandbox.pk )
            context.update({ 'portal_skus': pas_to_show })
    return rv

def _attach_user_to_account( request, session_key ):
    """
    Account requests use a temporary session object to pass account information,
    which is used to fix up the user with GA and potentially APA.
    """
    user = request.user
    sandbox = request.sandbox
    session = _cache.get( session_key )
    if not session:
        log.warning("SUSPECT - User add to GA missing session %s", session_key)
        return

    # Only allow session to be used once
    invalidate_key( session_key, 'session' )

    if session['sandbox'] != sandbox.id:
        log.warning("SUSPECT - User add to GA sandbox mismatch %s", session)
        return

    # Add user directly to existing license, handles account add if needed
    if session['apa_id']:
        apa = APA.objects.get_from_id( sandbox, session['apa_id'] )
        if apa and apa.add_ga_user( user ):
            log.info("GA APA invite: %s -> %s", request.mpipname, apa)
    else:
        # Add user to account if not already
        ga = GroupAccount.objects.get_from_id( sandbox, session['ga_id'] )
        if ga and ga.add_user( user ):
            log.info("GA invite: %s -> %s", request.mpipname, ga)

        # Add a license from coupon
        if session['coupon_slug']:
            coupon = Coupon.objects.coupon_search( sandbox, session['coupon_slug'] )
            if coupon and coupon.pa:
                apa = APA.objects.get_license_for_primary( user, coupon.pa,
                                                           coupon=coupon )
                if apa:
                    log.info2("GA coupon invite: %s -> %s", request.mpipname, apa)

def _check_user_pa( request, pa, context, coupon=None ):
    """
    For SKU and Coupon PA requests, the access options dialog will normally only
    be shown if there isn't access to the current PA, but this can be overridden.
    Staff mode always have access and never see the dialog.
    """
    user = request.user

    # Staff members don't have accounts, but will have access
    if user.access_staff:
        log.debug("SKU converted to staff access: %s -> %s", user, pa)
        context.update({ 'staff_access': True })
        return

    # See if the user already has APA for this PA or new APA can be created
    apa = None
    if user.au:
        # Find either APA that exists or can be created via requested sku and accounts
        for account in user.au.active_accounts:
            apa = process_new_license( user, pa, account, coupon )
            if apa:
                break

        # If the sku is free, no prompt, and accessible to account, try to apply it
        if not apa and pa.rules['no_prompt'] and pa.access_no_payment:
            free_access = pa.visible_to_links
            if not free_access:
                for account in user.au.active_accounts:
                    free_access = pa.visible_to_account( account )
                    if free_access:
                        break
            if free_access:
                new_apa = APA.objects.get_license_for_primary( user, pa )
                if new_apa:
                    apa = new_apa

    # Pass APA to portal startup; if not active, redirect to payment may be requested
    if apa:
        log.debug("Converting portal SKU to APA: %s -> %s -> %s", user, pa, apa)
        context.update({ 'portal_apa': apa })

    # No APA is available and prompt is on, trigger the SKU prompt on portal load
    # (note if payment redirect happens, this won't be used)
    if not apa or not apa.is_active( deep=True ):
        if not pa.rules['no_prompt']:
            log.debug("Setting up SKU prompt: %s -> %s", user, pa)
            context.update({ 'portal_skus': [ pa ] })

def _content_nav_start( request, content, context ):
    """
    Setup portal start state to navigate to content associated
    with this request.
    If Catalog/Content relationships are set up appropriately, this
    will be straightforward. In other cases, reasonable decisions
    about what to display will be attempted.
    """
    if content:
        log.debug2("Frame content: %s", content)
        content_id = None
        if safe_int( content ):
            content_id = content
        else:
            if isinstance( content, list ):
                content_id = _first_not_retired( content )
            else:
                content_id = content.pk
        if content_id:
            log.info2("Frame navigate to content id: %s", content_id)
            request.session['nav_to_content_id'] = content_id

    context['nav_to_content_id'] = request.session.get('nav_to_content_id')

def _first_not_retired( items ):
    if items:
        for item in items:
            if not item.is_retired:
                return item.pk
