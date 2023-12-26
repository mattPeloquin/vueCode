#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Group account admin licenses
"""
from django.template.response import TemplateResponse

from mpframework.common.cache.template import full_path_cache
from mpextend.user.usercontent.models import UserItem

from ...group import group_admin_view
from ._common import ga_admin_common


@full_path_cache
@group_admin_view
def ga_licenses( request, account=None ):
    """
    Screen for license display and analysis
    """
    account, context = ga_admin_common( request, account )

    # Get APA information for display and summary along with summary usage counts
    apa_rollups = {}
    for apa in account.get_apas():
        apa_rollups[ apa.pk ] = { 'started': 0, 'completed': 0, 'apa': apa }

    # Placeholder to track usages outside GA licenses
    other_uses = { 'started': 0, 'completed': 0, 'user_ids': set() }

    # Rollup usage data for tracking with APAs
    items = UserItem.objects.mpusing('read_replica')\
                .filter( cu__user_id__in=account.user_ids, top_tree__isnull=False )

    for ui in items.values( 'cu_id', 'progress', 'apa_id', 'last_used' ).iterator():

        apa_id = ui['apa_id']
        if apa_id in apa_rollups:
            accumulator = apa_rollups[ apa_id ]
        else:
            other_uses['user_ids'].add( ui['cu_id'] )
            accumulator = other_uses

        if ui['progress'] in ['C', 'A']:
            accumulator['completed'] += 1
        else:
            accumulator['started'] += 1

    other_uses['user_count'] = len( other_uses['user_ids'] )

    context.update({
        'apa_rollups': apa_rollups.values(),
        'other_uses': other_uses,
        })

    return TemplateResponse( request, 'group/licenses.html', context )
