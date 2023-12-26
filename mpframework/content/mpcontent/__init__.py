#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Content app

    Register content sandbox bootstrap
    Content uses time window caching where a baseline of each content type
    is cached, and then any deltas are transferred.
    This is implement in the function groups below by wrapping the
    calls in timewin caching.
"""

from mpframework import mpf_function_group_register


def _content_notime():
    # This is content small and stable enough to not use time window
    from .api import get_portal_types
    from .api import get_portal_groups
    from .api import get_portal_categories
    return [
        ( 'types', get_portal_types ),
        ( 'groups', get_portal_groups ),
        ( 'categories', get_portal_categories ),
        ]
mpf_function_group_register( 'bootstrap_content_notime', _content_notime )

def _content_timewin():
    # Snapshot of content from point of time, for cacheable URL
    from .api import get_trees
    from .api import get_items
    return [
        ( 'trees', get_trees ),
        ( 'items', get_items ),
        ]
mpf_function_group_register( 'bootstrap_content_timewin', _content_timewin )

def _content_delta():
    # Change in content since the snapshot
    from .api import get_trees
    from .api import get_items
    return [
        ( 'trees_delta', get_trees ),
        ( 'items_delta', get_items ),
        ]
mpf_function_group_register( 'bootstrap_content_delta', _content_delta )
