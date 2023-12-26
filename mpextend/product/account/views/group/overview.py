#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Group account admin dashboard
"""
from django.template.response import TemplateResponse

from mpframework.common.utils import week_incrementor
from mpframework.common.cache.template import full_path_cache
from mpframework.user.mpuser.models import mpUser
from mpextend.user.usercontent.models import UserItem

from ...group import group_admin_view
from ._common import ga_admin_common


RECENT_WEEKS = 8


@full_path_cache
@group_admin_view
def ga_overview( request, account=None ):
    """
    Screen proving chart rollups
    """
    account, context = ga_admin_common( request, account )
    user_ids = account.user_ids

    # Recent user activity histogram
    # Setup user activity based on recent weeks, get all users for ranking
    # while just a count of older users
    cutoff, user_weeks, user_increment = week_incrementor( RECENT_WEEKS )
    user_tracking = mpUser.objects.mpusing('read_replica')\
                        .select_related('tracking')\
                        .filter( id__in=user_ids )

    for last_update in user_tracking\
                    .filter( tracking__last_update__gt=cutoff )\
                    .values_list( 'tracking__last_update', flat=True ).iterator():
        user_increment( last_update )

    last_uses = {}
    last_uses.update( sorted( user_weeks.items(), key=lambda t: t[0], reverse=True ) )
    uses = {
        'user_count': len( user_ids ),
        'data': {
            'labels': list( last_uses ),
            'series': [ list( last_uses.values() ) ],
            }
        }

    # Rollup usage data for tracking in total, recent weeks
    started = 0
    completed = 0
    older_items = 0
    item_weeks = {}
    cutoff, item_weeks, item_increment = week_incrementor( RECENT_WEEKS )
    items = UserItem.objects.mpusing('read_replica')\
                    .filter( cu__user_id__in=user_ids, top_tree__isnull=False )

    for ui in items.values( 'cu_id', 'progress', 'apa_id', 'last_used' ).iterator():

        if ui['last_used'] < cutoff:
            older_items += 1
        else:
            item_increment( ui['last_used'] )

        if ui['progress'] in ['C', 'A']:
            completed += 1
        else:
            started += 1

    completion = {
        'total': started + completed,
        'data': {
            'labels': [ "{} in progress".format( started ), "{} completed".format( completed ) ],
            'series': [ started, completed ],
            }
        }

    item_uses = {}
    item_uses.update( sorted( item_weeks.items(), key=lambda t: t[0], reverse=True ) )
    usage_time = {
        'data': {
            'labels': list( item_uses ),
            'series': [ list( item_uses.values() ) ],
            }
        }

    # Top collection histogram
    # Look at the top collection usage to summarize most used
    top_usage = {}
    tops = UserItem.objects.mpusing('read_replica')\
                    .select_related( 'cu', 'item' )\
                    .filter( cu__user_id__in=user_ids, top_tree__isnull=True )
    for name in tops.values_list( 'item___name', flat=True ).iterator():
        top_usage[ name ] = top_usage.get( name, 0 ) + 1
    top_uses = dict( sorted( top_usage.items(), key=lambda t: t[1], reverse=True )[:4] )
    top_uses = dict( sorted( top_uses.items(), key=lambda t: t[1] ) )
    usage_content = {
        'data': {
            'labels': list( top_uses ),
            'series': [ list( top_uses.values() ) ],
            }
        }

    # Package it up for template
    context.update({
        'uses': uses,
        'completion': completion,
        'usage_content': usage_content,
        'usage_time': usage_time,
        })
    return TemplateResponse( request, 'group/overview.html', context )
