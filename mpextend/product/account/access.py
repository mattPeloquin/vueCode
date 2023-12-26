#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared Logic for linking content, catalog, and user account licenses
"""

from mpframework.common import log
from mpframework.common.tags import tag_match
from mpframework.common.utils import tz_strip
from mpframework.common.utils import DATETIME_FUTURE
from mpframework.common.utils import json_dump
from mpframework.common.logging.timing import mpTiming
from mpextend.product.catalog.utils import public_pas
from mpextend.product.catalog.utils import free_pa_content

from .models import APA
from .utils import get_au


def _check_existing_license( item, user ):
    """
    Check if user last used content with an APA that is valid:
     - Avoids searching for APA match
     - Required to support usage metering
    """
    from mpextend.user.usercontent.models import UserItem
    ui = UserItem.objects.get_user_item( user, item )
    if ui and ui.apa_id:
        apa = APA.objects.get_from_id( user.sandbox, ui.apa_id )
        if apa.is_active( save=True, deep=True ):
            return apa

def get_apa_dicts( user ):
    """
    Provide key info from active APAs for the user
    """
    rv = []
    if user.au:
        for apa in user.au.active_apas():
            rv.append({
                'id': apa.pk,
                'sku': apa.pa.sku,
                'includes_all': apa.includes_all,
                'tags': [ str( tag ).strip().lower() for tag in apa.tags ],
                'is_trial': apa.is_trial,
                })
    log.debug2("ACTIVE APAs: %s -> %s", user, rv)
    return rv

def process_new_license( user, pa, account, coupon=None, units=None ):
    """
    Shared processing for PA URL/SKU requests
    Determines access and sets up payment apa if needed.
    Handles coupons and allowing staff access to all content.
    Returns:
        False - access is not possible (visitor/staff user view)
        None - access cannot be had (e.g., a one-time free PA is used up)
        apa - If APA active, access is granted, if not, payment is needed
    """
    log.info2("Access request: %s, %s -> c(%s) pa(%s)", user, account, coupon, pa)
    assert user and pa

    if not user.is_ready():
        log.info3("Anon/not ready access, probably session expired: %s - %s", user, pa)
        return False

    if user.access_staff:
        log.info3("Staff access denied due to user view: %s -> %s", user, pa)
        assert user.staff_user_view
        return False

    if not account:
        log.warning("ACCESS ERROR - Non-staff user with no account: %s -> %s", user, pa)
        return False

    # Get license if it exists, or create a new one
    # New licenses will be pending or immediate depending on price/options
    apa = APA.objects.get_license( user, account, pa, coupon=coupon, units=units,
                                    activate=False )
    if not apa:
        log.info("ACCESS DENIED - APA used up or not created: %s -> %s", user, pa)
    else:
        if not apa.is_active( deep=True ):
            log.info2("Payment needed to activate APA: %s -> %s", user, apa)

    return apa

def quick_access_check( user, item, content_tags=False ):
    """
    Optimized content item access check against free offerings and user's APAs.
    Returns True or list of APAs if user has access.
    TRUTHY response is GAURANTEED ACCURATE - False doesn't mean access
    isn't granted; just that a a full check is needed.
    Assumes content_tags is stripped lower case.
    Will calculate content_tags if not passed in.
    """
    assert item and user
    rv = False
    if user.au:
        # If tags not provided, get all tags for item
        if content_tags is False:
            content_tags = item.my_tags()
        # See if any existing APAs apply
        apas = []
        for apa in user.au.active_apas():
            if apa.is_trial and item.sb_options['portal.no_trials']:
                continue
            if not apa.room_for_item( item ):
                continue
            if apa.includes_all:
                apas.append( apa )
                continue
            for tag in content_tags:
                if tag_match( tag, apa.tags ):
                    apas.append( apa )
                    continue
        rv = apas if apas else rv

    log.debug2("quick_access_check: %s -> %s, %s", user, rv, item)
    return rv

def content_access_data( item, user ):
    """
    All mpExtend checks for APA access to content are processed here.

    Returns access rights for the user to the given content, including
    finding any apas and pas that connect the user to the content.
    This information is prepared for sending to the to the web UI for
    decisions about granting access and available PAs:

        1) If access is valid 'can_access' is true:
          - If APA relationship is clear, 'apa_to_use' is set to APA ID
          - 'apas' is list of active APA IDs, if any

        2) Otherwise 'can_access' is false:
          - 'pas' is list of visible PA IDs, if any
          - user account information
    """
    assert item and user

    # If in staff testing view, force access dialog
    if user.staff_user_view:
        log.debug2("Staff user view deny access: %s -> %s", user, item)

    # If the user already has accessed with an active APA, just keep using.
    # Necessary for usage metering, and is reasonable for other
    # scenarios even if there are edge cases where it might be better
    # for user to be switched to a new free APA.
    else:
        apa = _check_existing_license( item, user )
        if apa:
            return {
                'can_access': True,
                'apa_to_use': apa.pk,
                'description': apa.name,
                }

    # Get active APAs and available PAs for user's access to content
    rv = { 'can_access': False }
    try:
        # If quick check positive hit, go with those apas
        access = quick_access_check( user, item )
        if access:
            log.debug("Quick access hit: %s, %s", user, access)
            apas = access
            pas = []
        # If no easy access, do deep check
        else:
            log.debug("Deep access check: %s -> %s", user, item)
            apas, pas = _product_relationships( item, user )

        # Remove any APAs that don't have room
        apas = [ a for a in apas if a.room_for_item( item ) ]

        # If apas are present here, they are valid - select best default based
        # on free and expiration
        apas.sort( key=lambda apa:( apa.access_price,
                    tz_strip(apa.access_end) or DATETIME_FUTURE ) )
        apa_to_use = apas[0] if apas else None

        # If no access but a free no prompt PA exists, use it
        if not apa_to_use:
            free_apa = _create_first_auto_free_apa( user, pas )
            if free_apa:
                apas.append( free_apa )
                apa_to_use = free_apa

        # Setup access parameters
        can_access = bool( apa_to_use )
        rv.update({ 'can_access': can_access })

        # If valid APAs already in place, user may need to pick one
        # Otherwise, send PA and account info so user can create an APA
        if can_access:
            rv.update( _pack_access_data( apa_to_use, apas ) )
        else:
            rv.update( _pack_access_options( pas, user ) )

    except Exception:
        log.exception("content_access_data: %s -> %s", user, item)
    return rv

def content_access_options( item, user ):
    """
    Returns the access options for the given content and user
    """
    _apas, pas = _product_relationships( item, user )
    return _pack_access_options( pas, user )

def _product_relationships( content_item, user ):
    """
    Complete check on user access and purchase options.
    Returns ALL active APAs and PAs for a SINGLE content item and user.

    Because looking at all access options for a content item and user
    is expensive, the ultimate check for whether user has access
    is combined with figuring out purchase options.

    This is separate from quick_access_check; that is used
    as an optimized check, but is not the final say on access.

    Returned lists are designed to easily support tree recursion and
    conversion to dict, as they are for JSON access data in client JS.
    """
    au = get_au( user )
    if log.debug_on():
        t = mpTiming()
        log.debug("START ACCESS CHECK %s -> %s", au, content_item)

    # Get set of potential PAs upfront
    available_pas = au.available_pas if au else public_pas( user.sandbox.pk )
    log.debug2("Available PAs for au(%s): %s", au, available_pas)

    # If no content item, provide entire set of PAs
    if content_item:
        apas, pas = _find_apas_and_pas( content_item, au, available_pas )
    else:
        apas = []
        pas = available_pas

    # Sort PAs to provide free, longer ones first
    pas.sort( key=lambda pa:( pa.access_price or 0, pa.access_period_minutes or 0 ) )

    if log.debug_on():
        log.debug("ACCESS PAs | APAs: %s %s -> %s | %s", user, content_item, pas, apas)
        log.debug("END ACCESS CHECK( %s ) %s -> %s", t, user, content_item)
    return apas, pas

def _find_apas_and_pas( content_item, au, available_pas ):
    """
    Add PAs and APAs for an item and any tree nodes it belongs to
    """
    apas = set()
    pas = set()
    tags_to_skip = []
    if log.debug_on():
        depth = []

    def _process( item ):
        # If this is a tree node, recurse through any parent nodes first
        if item.is_collection:
            item = item.downcast_model
            log.detail3("PARENT RELATIONSHIP: %s -> %s", item, item.parent)
            _recurse( item.parent )
        # If a content item, recurse any tree node relationships first
        else:
            log.detail3("NODE RELATIONSHIP: %s -> %s", item, item.my_tree_nodes)
            for node in item.my_tree_nodes:
                _recurse( node )

        # To limit overlapping checking during recursion, keep track of tags
        # that have already been considered
        if item.tag in tags_to_skip:
            log.debug2("Content tag considered, skipping: %s", item.tag)
            return
        tags_to_skip.append( item.tag )

        # Add any available PAs and active APAs that match content tag
        pas.update([ pa for pa in available_pas if pa.matches_tag( item.tag ) ])
        apas.update( au.active_apas( (item.tag,) ) if au else [] )

    def _recurse( next_item ):
        # Recurse to next dependent item, handle base case
        if not next_item:
            return
        if log.debug_on():
            t = mpTiming()
            depth.append( next_item )
            log.debug2("---> Start item (depth=%s): %s", len(depth), next_item)

        _process( next_item )

        if log.debug_on():
            log.debug2("<--- Finish item %s: %s", t.log_total, depth.pop())

    # Search from the item up the tree, adding apas and pas
    _recurse( content_item )

    if content_item.sb_options['portal.no_trials']:
        # Remove trial items if content doesn't allow trial access
        # Do this at the end instead of during processing to keep things simple
        # regarding the potential dependency relationships
        log.debug("Removing trial apas and pas: %s -> %s", au, content_item)
        apas = [ apa for apa in apas if not apa.is_trial ]
        pas = [ pa for pa in pas if not pa.is_trial ]
    else:
        apas = list( apas )
        pas = list( pas )

    return apas, pas

def _create_first_auto_free_apa( user, pas ):
    """
    If there are any PAs that are free, can be applied silently,
    and don't have a prior use limitation, create an apa
    using the user's primary account.
    """
    if user.is_ready():
        for pa in pas:
            if ( pa.visible_to_all and pa.rules['no_prompt'] and
                    pa.access_no_payment ):
                log.info2("NEW FREE APA: %s -> %s", user, pa)
                new_apa = APA.objects.get_license_for_primary( user, pa )
                return new_apa or None

def _pack_access_data( apa_to_use, apas ):
    """
    Package access info for client UI via JSON
    """
    assert apas

    # All apa information is sent so UI can give option to choose
    apa_dict = {}
    for apa in apas:
        apa_dict[ apa.pk ] = apa.json()

    return {
        'apa_to_use': apa_to_use.pk,
        'description': apa_to_use.name,
        'default_mode': apa_to_use.default_mode,
        'apas': json_dump( apa_dict ),
        }

def _pack_access_options( pas, user ):
    """
    Setup product access options for UI JSON
    """
    pa_dict = {}
    for pa in pas:
        pa_dict[ pa.sku ] = pa.json()

    # The access UI can handle more than one account being used
    # with a user, or no accounts for staff user spoof mode
    account_dict = {}
    if user.au:
        account = user.au.primary_account
        extra_info = {
            'order': 1,
            'admin': account.has_owner( user ),
            }
        account_dict = {
            account.id: account.json( extra_info ),
            }

    return {
        'pas': json_dump( pa_dict ),
        'accounts': json_dump( account_dict ),
        }
