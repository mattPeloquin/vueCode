#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared code to rollup user item info by top content

    User item tracking is based on the user's last interaction with the
    content item. Some reporting such as points and is_required depend
    on current settings in the item or its relationship to the tree
    where the item was used. This code blends the optimized usercontent
    information in the user block with the current state of the top trees.

    The special case of treeless items (e.g., for portal with no collections)
    is also handled.
"""
from django.conf import settings

from mpframework.common.cache import cache_rv
from mpframework.content.mpcontent.models import Tree
from mpframework.content.mpcontent.models import BaseItem
from mpframework.content.mpcontent.cache import cache_group_content


# Shared columns added for top content rollups based on content and user data
_report_top_rollup = {
    'Required items':     lambda tc:  len(tc['req_items']),
    'Items in progress':  lambda tc:  tc['started'],
    'Required complete':  lambda tc:  tc['req_completed'],
    'Percent complete':   lambda tc:  "" if not tc['req_points'] else
            round( float(tc['req_comp_points']) / float(tc['req_points']), 2 ),
    'Total items':        lambda tc:  len(tc['items']),
    'Items complete':     lambda tc:  tc['completed'],
    'Required points':    lambda tc:  tc['req_points'],
    'Req pts complete':   lambda tc:  tc['req_comp_points'],
    'Required size':      lambda tc:  tc['req_size'],
    'Req size complete':  lambda tc:  tc['req_comp_size'],
    'Total points':       lambda tc:  tc['points'],
    'Points complete':    lambda tc:  tc['comp_points'],
    'Total size':         lambda tc:  tc['size'],
    'Size complete':      lambda tc:  tc['comp_size'],
    }

def top_usercontent_headers():
    return list( _report_top_rollup )

def top_usercontent_add( ui, totals ):
    """
    Given a useritem for a top tree, returns list of report column values
    for the given user item data row.
    'totals' is dict returned from top_usercontent_totals.
    """
    return [ fn( totals[ ui['item_id'] ] ) for
                fn in _report_top_rollup.values() ]

def top_usercontent_totals( user ):
    """
    Given a user from a report userblock, return dict keyed by top collection
    id with rollup of content and user content data.
    """
    rv = {}
    # First setup content totals for user's items
    for ui in user.usertops:
        top = ui['item_id']
        rollup = _content_rollup( user._provider, top )
        # Add usage info for non-collection items
        if not ui['is_tree']:
            _add_usercontent( ui, rollup )
        rv[ top ] = rollup
    # Then add rollups for all the user's usage data under tops
    for ui in user.useritems:
        top = rv.get( ui.get('top_id') )
        if top:
            _add_usercontent( ui, top )
    return rv

@cache_rv( keyfn=lambda provider, item_id:(
            item_id, cache_group_content( provider.pk ) ) )
def _content_rollup( provider, item_id ):
    """
    Given a top collection return dict with totals for items in the collection.
    If item_id is for collectionless item, return values for that.
    """
    rv = {
        # Values defined by content metadata, which are calculated here
        'items': [], 'req_items': [],
        'size': 0, 'req_size': 0,
        'points': 0, 'req_points': 0,
        'nodes': 0,
        # User usage values rolled up later by _add_usercontent
        'started': 0, 'minutes': 0, 'uses': 0,
        'completed': 0, 'comp_size': 0, 'comp_points': 0,
        'req_completed': 0, 'req_comp_size': 0, 'req_comp_points': 0,
        'feedback': 0, 'update_manual': 0,
        }
    try:
        # Totals are normally top-collection rollups
        top = Tree.objects.get( _provider=provider, id=item_id, parent__isnull=True )
        for item in top.all_items():
            # Don't include default points for nested tree nodes
            # Tree nodes normally shouldn't have size or points, but support adding
            # them in if they are present -- DON'T USE NODE SIZE/POINTS for totals
            default_points = 0 if item.is_collection else 1
            points = ( default_points if item.points is None else item.points )
            size = ( 0 if item.size is None else item.size )
            rv['size'] += size
            rv['points'] += points
            if item.is_collection:
                rv['nodes'] += 1
            else:
                rv['items'].append( item.pk )
                if item.required:
                   rv['req_items'].append( item.pk )
                   rv['req_size'] += size
                   rv['req_points'] += points
    except Tree.DoesNotExist:
        # Handle the case of individual content without a collection
        item = BaseItem.objects.get( _provider=provider, id=item_id )
        rv['items'].append( item.pk )
        rv['req_items'].append( item.pk )
        rv['nodes'] = 1
        rv['points'] = 1 if item.points is None else item.points
    return rv

def _add_usercontent( ui, tc ):
    """
    Add the user item usage information to the given top content rollup dict
    """
    assert not ui['is_tree']
    assert ui['item_id'] in tc['items']
    comp = 1 if ui['is_complete'] else 0
    comp_size = ui['size'] if ui['is_complete'] else 0
    comp_points = ui['points'] if ui['is_complete'] else 0
    tc.update({
        'started': tc['started'] + ( 1 if ui['progress'] in 'S' else 0 ),
        'minutes': tc['minutes'] + ( ui['seconds_used'] // 60 ),
        'uses': tc['uses'] + ui['uses'],
        'feedback': tc['feedback'] + ( 1 if ui['feedback'] else 0 ),
        'update_manual': tc['update_manual'] + (
                1 if ui['progress_update'] in 'UA' else 0 ),
        'completed': tc['completed'] + comp,
        'comp_size': tc['comp_size'] + comp_size,
        'comp_points': tc['comp_points'] + comp_points,
        })
    if ui['item_id'] in tc['req_items']:
        tc.update({
            'req_completed': tc['req_completed'] + comp,
            'req_comp_size': tc['req_comp_size'] + comp_size,
            'req_comp_points': tc['req_comp_points'] + comp_points,
            })
