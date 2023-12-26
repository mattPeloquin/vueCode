#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Group account admin usage
"""
from django.template.response import TemplateResponse

from mpframework.common import log
from mpframework.common.cache.template import full_path_cache
from mpframework.user.mpuser.models import mpUser
from mpextend.user.usercontent.models import UserItem

from ...group import group_admin_view
from ._common import ga_admin_common


@full_path_cache
@group_admin_view
def ga_users_summary( request, account ):
    """
    Screen with per-user summary and report buttons
    """
    account, context = ga_admin_common( request, account )
    user_ids = account.user_ids

    usage = {}
    def _aggregate_usage( items, started, completed, minutes=None ):
        totals = { 'all': 0, started: 0, completed: 0 }
        for ui in items.values( 'cu__user_id', 'progress', 'seconds_used' ).iterator():
            totals['all'] += 1
            user = ui['cu__user_id']
            use = usage.get( user, { started: 0, completed: 0 } )
            if ui['progress'] in 'S':
                use[ started ] = use.get( started, 0 ) + 1
                totals[ started ] = totals.get( started, 0 ) + 1
            if ui['progress'] in 'CA':
                use[ completed ] = use.get( completed, 0 ) + 1
                totals[ completed ] = totals.get( completed, 0 ) + 1
            if minutes:
                use[ minutes ] = use.get( minutes, 0 ) + ( ui['seconds_used'] // 60 )
            usage[ user ] = use
        return totals

    # Get summary of top-level collection usage
    tops = UserItem.objects\
                    .mpusing('read_replica')\
                    .select_related( 'cu', 'item' )\
                    .filter( sandbox=request.sandbox, cu__user_id__in=user_ids,
                             top_tree__isnull=True )
    totals_tops = _aggregate_usage( tops, 'tops_started', 'tops_completed', 'minutes' )
    log.info2("Completed rollup %s, %s tops for %s",
                    request.mptiming, totals_tops['all'], request.mpipname )

    # Add item usage
    items = UserItem.objects\
                    .mpusing('read_replica')\
                    .select_related( 'cu', 'item' )\
                    .filter( sandbox=request.sandbox, cu__user_id__in=user_ids,
                             top_tree__isnull=False )
    totals_items = _aggregate_usage( items, 'items_started', 'items_completed' )
    log.info2("Completed rollup %s, %s items for %s",
                    request.mptiming, totals_items['all'], request.mpipname )

    # Add usage data to each user entry
    users = []
    account_users = mpUser.objects.mpusing('read_replica')\
                        .select_related('tracking')\
                        .filter( id__in=user_ids )
    for user in account_users.iterator():
        try:
            info = user.dict
            info.update( usage.get( user.pk, {} ) )
            users.append( info )
        except Exception as e:
            log.warning_quiet("Error in user row for GA usage: %s -> %s", user, e)

    context.update({
            'users': users,
            'totals_items': totals_items,
            'totals_tops': totals_tops,
            })
    return TemplateResponse( request, 'group/users.html', context )
