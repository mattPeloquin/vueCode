#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Content context to add to templates
"""

from .models import PortalType


def content( request ):
    if request.is_healthcheck or request.is_bad:
        return {}
    context = _types( request )
    return context

def _types( request ):
    """
    If user can see and has defined custom item types, load them to template with
    metadata so they can show in menus.
    """
    user = request.user
    items = []
    trees = []
    only_items = []
    only_trees = []
    if user.access_high:
        for pt in PortalType.objects.get_portal_objs( request ):
            obj = {
                'id': pt.pk,
                'name': pt.name,
                }
            if pt.scope == 'C':
                trees.append( obj )
                only_trees.append( obj )
            elif pt.scope == 'I':
                items.append( obj )
                only_items.append( obj )
            else:
                trees.append( obj )
                items.append( obj )
    return {
        'item_types': items,
        'tree_types': trees,
        'item_only_types': only_items,
        'tree_only_types': only_trees,
        }
