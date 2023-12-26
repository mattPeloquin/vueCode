#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared code to rollup user item information for each user
"""

_content_top = {
    'Collections completed': lambda rollup: rollup['top_complete'],
    'Collections used':      lambda rollup: rollup['top_used'] if rollup['top_used'] else '',
    'Content minutes':       lambda rollup: rollup['minutes'],
    'Content hours':         lambda rollup: rollup['minutes'] // 60,
    }
_content_items = {
    'Items completed':      lambda rollup: rollup['items_complete'],
    'Items viewed':         lambda rollup: rollup['items_used'],
    'Completed minutes':    lambda rollup: rollup['minutes_complete'],
    'Completed hours':      lambda rollup: rollup['minutes_complete'] // 60,
    }

def content_headers( items=True ):
    rv = list( _content_top )
    if items:
        rv += list( _content_items )
    return rv

def content_row_items( user, items=True ):
    """
    Rollup user items in one loop, return dict for reporting lambdas
    Only top-level collections and items are considered (sub collections ignored)
    """
    rollup = {
        'minutes': 0,
        'minutes_complete': 0,
        'top_minutes_complete': 0,
        'top_used': 0,
        'top_complete': 0,
        'items_used': 0,
        'items_complete': 0,
        'items_minutes': 0,
        }

    columns = _content_top.copy()
    for ui in user.usertops:
        rollup['top_used'] += 1
        rollup['minutes'] += ui['minutes_used']
        if ui['is_complete']:
            rollup['top_complete'] += 1
            rollup['top_minutes_complete'] += ui['minutes_used']

    if items:
        columns.update( _content_items )
        for ui in user.useritems:
            rollup['items_used'] += 1
            rollup['items_minutes'] += ui['minutes_used']
            if ui['is_complete']:
                rollup['items_complete'] += 1
                rollup['minutes_complete'] += ui['minutes_used']

    return [ fn( rollup ) for fn in columns.values() ]
