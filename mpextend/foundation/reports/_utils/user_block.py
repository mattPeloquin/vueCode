#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Optimized DB access for data organized by users; this is used
    for the bulk of reporting.
"""
from collections import defaultdict
from django.conf import settings
from django.db.utils import OperationalError
from django.contrib.contenttypes.models import ContentType

from mpframework.common import log
from mpframework.common.tasks import spool_breathe
from mpframework.common.utils import timedelta_past
from mpframework.common.utils import seconds_to_minutes
from mpframework.user.mpuser.models import mpUser
from mpextend.product.account.models import APA
from mpextend.user.usercontent.models import UserItem


def define_user_blocks( sandbox_id, size, start=None ):
    """
    Return list of id blocks for all sandbox users active since start
    """
    user_qs = mpUser.objects.mpusing('read_replica')\
                   .filter( _sandbox_id=sandbox_id )\
                   .filter( _staff_level__isnull=True )\
                   .order_by('id')
    if start:
        start_date = timedelta_past( days=int(start) )
        user_qs = user_qs.filter( tracking__last_update__gte=start_date )
    user_ids = user_qs.values_list( 'id', flat=True )
    return _get_blocks( user_ids, size )

def get_account_user_blocks( account, size ):
    """
    Return list of id blocks for all group account users
    """
    user_ids = account.group_account.users.all().values_list( 'user_id', flat=True )
    return _get_blocks( user_ids, size )

def _get_blocks( ids, size ):
    """
    Break down list of ids into a list of lists chunked by size
    """
    return [ ids[ pos:pos + size ] for pos in
                range( 0, len( ids ), size ) ]

def get_user_block_info( sandbox_id, user_ids=None, timing=None, detailed=False ):
    """
    Returns dict with a block of user objects indexed by user id
    These user objects include additional dicts and lists with expensive
    information related to usage, accounts, and apas for all user reporting.

    Not all reports will use all the data, but always compile it for
    the sake of code simplicity and flexibility in report writing.

    FUTURE - find way to make management of group accounts more efficient
    by processing users for group accounts in the same block.
    """
    log.debug_on() and log.debug("GETTING USER BLOCK: %s -> %s, %s",
                        timing, sandbox_id, len(user_ids) if user_ids else "all")

    # Get core user objects with account and tracking info
    user_qs = mpUser.objects.mpusing('read_replica')\
                  .select_related( 'account_user',
                                   'account_user__primary_account',
                                   'tracking' )\
                  .filter( _sandbox_id=sandbox_id )
    if user_ids:
        user_qs = user_qs.filter( id__in=user_ids )

    users = {}
    grp_account_ids = set()
    indv_account_ids = set()

    # Make first pass through the users to setup user dict and populate account info
    for user in user_qs.iterator():
        log.debug_on() and log.detail3("adding user: %s -> %s", user.pk, user.email)

        users[ user.pk ] = user

        # Add account to user and account sets
        user.account = None
        if hasattr( user, 'account_user' ):
            try:
                primary = user.account_user.primary_account
                if primary:
                    user.account = primary
                    if primary.is_group:
                        grp_account_ids.add( primary.pk )
                    else:
                        indv_account_ids.add( primary.pk )

                elif not user.is_staff:
                    log.info3("User has no primary account: %s", user)
            except OperationalError:
                # Most likely DB connection needs reset, let caller manage
                raise
            except Exception as e:
                log.info2("Error attaching user account: %s -> %s", user, e)
                if settings.MP_TESTING:
                    raise

        # Optimize tracking data access
        user.geo = user.tracking.geoip

    log.debug_on() and log.debug2("ADDED BLOCK USERS: %s -> %s users", timing, len(users))

    # Get APA and useritem instances for every account
    _, apas_account = _get_users_apas( sandbox_id, user_ids,
                                       grp_account_ids, indv_account_ids )
    tops, items, mins = _get_users_useritems( sandbox_id, user_ids )
    log.debug_on() and log.debug2("PREPARED USER INFO: %s -> %s users", timing, len(users))

    # Make second pass to add usage and APA information
    for user in users.values():
        log.debug_on() and log.detail3("adding user info: %s -> %s", user.pk, user.email)

        # Usage information
        user.usertops = tops[ user.pk ]
        user.useritems = items[ user.pk ]
        user.total_mins = mins[ user.pk ]

        # APAs, indexed by account
        user_apas = {}
        if user.account:
            for apa in apas_account[ user.account.pk ]:
                # For group accounts, add APAs user is part of
                if user.account.is_group:
                    if apa.group_users:
                        if user.pk in apa.group_users:
                            user_apas[ apa.pk ] = apa
                    else:
                        user_apas[ apa.pk ] = apa
                # For individual account, add all APAs
                else:
                   user_apas[ apa.pk ] = apa
        user.apas = user_apas

    log.debug_on() and log.debug("USER BLOCK PREPARED: %s -> %s users", timing, len(users))
    return {
        'users': users,
        'ga_ids': grp_account_ids,
        'ia_ids': indv_account_ids,
        }

def _get_users_useritems( sandbox_id, user_ids ):
    """
    Return dict of all usage rows for both top and sub items
    for the given users.
    Tops returns top-level collections AND items used with no collection.
    If false, returns items that are inside collections.

    HACK - for performance, only the information needed for useritems is
    retrieved, and it is placed in a dict instead of models, and different
    values may be placed depending on whether for a top or item
    DOWNSTREAM USE MUST ENSURE INFO USED IS ADDED HERE
    """
    spool_breathe()
    log.debug_on() and log.debug("Geting usage info: %s users",
                                len(user_ids) if user_ids else "all")
    filter = {
        'sandbox_id': sandbox_id,
        'uses__gte': 1,     # Only include initialized records in reporting
        }
    if user_ids:
        filter.update({ 'cu__user_id__in': user_ids })

    qs = UserItem.objects.mpusing('read_replica')\
                .select_related( *_ui_related )\
                .filter( **filter )\
                .values( *_ui_values )
    usertops = defaultdict( list )
    useritems = defaultdict( list )
    totalmins = defaultdict( int )
    for ui in qs.iterator():
        try:
            userid = ui['cu__user_id']
            tops = not bool( ui['top_tree_id'] )
            ui['ctype'] = ContentType.objects.get_for_id(
                        ui['item___django_ctype_id'] ).model
            ui['is_tree'] = bool( 'tree' == ui['ctype'] )
            log.debug_on() and log.detail3("adding user%s %s: %s -> %s",
                        "top" if tops else "item", ui['id'], ui['ctype'], userid)

            # Make convenient short names for reporting
            ui['name'] = ui['item___name']
            ui['tag'] = ui['item__tag'] or ''
            ui['internal'] = ui['item__internal_tags'] or ''
            ui['is_complete'] = ui['progress'] in 'CA'
            ui['minutes_used'] = seconds_to_minutes( ui['seconds_used'] )
            ui['portal_type'] = ui['item__portal_type___name'] or ''
            if ui['is_tree']:
                totalmins[ userid ] += ui['minutes_used']
            else:
                ui['top_id'] = ui['item_id'] if tops else ui['top_tree__item_id']
                ui['top_name'] = '' if tops else ui['top_tree__item___name']
                ui['size'] = ui['item__size'] or 0
                ui['points'] = ui['item___points'] or 1

            (usertops if tops else useritems)[ userid ].append( ui )

        except OperationalError:
            # Most likely DB connection needs reset, let caller manage
            raise
        except Exception:
            log.exception_quiet("Exception packing useritem: %s", ui )
            if settings.MP_TESTING:
                raise

    log.debug_on() and log.debug("Got content usage, users in tops and items: %s, %s",
                                len(usertops), len(useritems))
    return usertops, useritems, totalmins

_ui_values = ( 'id', 'progress', 'seconds_used', 'uses', 'feedback', 'apa_id',
            'last_used', 'hist_created', 'completed', 'progress_update',
            'cu__user_id',
            'top_tree_id', 'top_tree__item_id', 'top_tree__item___name',
            'item_id', 'item___name', 'item__tag', 'item__internal_tags',
            'item__size', 'item___points', 'item__portal_type___name',
            'item___django_ctype_id',
            )
_ui_related = ( 'cu', 'item', 'item__portal_type',
            'top_tree', 'top_tree__item' )

def _get_users_apas( sandbox_id, user_ids, grp_account_ids, indv_account_ids ):
    """
    Returns dicts of APA object lists, one indexed by id, and one by account id
    """
    spool_breathe()
    log.debug_on() and log.debug("Getting APAs for users: users(%s) -> grp(%s), indv(%s)",
                        len(user_ids), len(grp_account_ids), len(indv_account_ids))
    apas_id = {}
    apas_account = defaultdict( list )

    def set_rv( apa ):
        apas_id[ apa.pk ] = apa
        apas_account[ apa.account_id ].append( apa )

    apa_qs = APA.objects.mpusing('read_replica')\
                .select_related( 'pa', 'account' )

    # Individual accounts
    qs = apa_qs.filter( sandbox_id=sandbox_id, is_activated=True,
                account_id__in=indv_account_ids )
    for apa in qs.iterator():
        apa.group = False
        apa.group_users = False
        set_rv( apa )

    # All-user group accounts
    qs = apa_qs.filter( sandbox_id=sandbox_id, is_activated=True,
                account_id__in=grp_account_ids, ga_users__isnull=True )
    for apa in qs.iterator():
        apa.group = True
        apa.group_users = False
        set_rv( apa )

    # Specific user group accounts
    qs = apa_qs.filter( sandbox_id=sandbox_id, is_activated=True,
                account_id__in=grp_account_ids )
    if user_ids:
        qs = qs.filter( ga_users__user_id__in=user_ids )
    for apa in qs.iterator():
        apa.group = True
        apa.group_users = [ gu.user_id for gu in apa.ga_users.all() ]
        set_rv( apa )

    log.debug_on() and log.debug("Got user block APAs: %s", len(apas_id))
    return apas_id, apas_account
