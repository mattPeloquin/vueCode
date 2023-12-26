#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Content Items API

    FUTURE - Optimize initial item loading with values lists; would
    need a fake object that can do url paths
"""

from mpframework.common import log
from mpframework.common.api import respond_api_call
from mpframework.common.view import staff_required

from ..models import BaseItem
from ..models import get_content_item_models
from ..utils import content_search
from ._utils import get_baseitem_values
from ._utils import get_tree_values
from .bootstrap import *


def get_content( request ):
    """
    Return all public content for the sandbox.
    """
    def handler( _get ):
        return {
            'categories': get_portal_categories( request ),
            'types': get_portal_types( request ),
            'groups': get_portal_groups( request ),
            'collections': get_trees( request ),
            'items': get_items( request ),
            }
    return respond_api_call( request, handler, methods=['GET'] )

def content_full( request, content_slug=None ):
    """
    Return all metadata for an item. Used both as public API for public content
    and in some cases by portal for info not loaded during bootstrap.
    If content_slug doesn't exist, return blank to discourage probing.
    """
    def handler( _get ):
        return _get_content( request, content_slug, True )
    return respond_api_call( request, handler, methods=['GET'] )

def content_partial( request, content_slug=None ):
    """
    Return descriptive content metadata
    """
    def handler( _get ):
        return _get_content( request, content_slug, False )
    return respond_api_call( request, handler, methods=['GET'] )

def _get_content( request, content_slug, full ):
    if content_slug:
        item = content_search( request, content_slug )
        if item:
            if item.is_collection:
                node = item.downcast_model
                values = get_tree_values( node, full_load=full )
            else:
                values = get_baseitem_values( item, full_load=full )
            return values

@staff_required
def item_add( request ):
    """
    Add a new item to the sandbox, with the option to:
      - Specify a type and an optional name OR
            use an existing item as shallow or deep clone
      - Optionally add to a tree node
    """
    def handler( payload ):
        item_type = payload.get('item_type')
        clone_id = payload.get('clone_id')
        tree_id = payload.get('tree_id')
        log.info2("API item add: %s -> %s, %s, %s", request.mpipname, item_type,
                    clone_id, tree_id)

        # Create clone or new placeholder item
        if clone_id:
            source = BaseItem.objects.active()\
                        .get( request=request, id=clone_id )\
                        .downcast_model
            name = source.name + u" copy"
            new_item = source.clone( sandbox=request.sandbox, name=name,
                        full_clone=payload.get('full_clone') )
        else:
            klass = get_content_item_models()[ item_type ]
            name = payload.get('name')
            if not name:
                # HACK - use a well-known, UI reasonable, name for new item
                content_name = getattr( klass._meta, 'verbose_name', u"content" )
                name = u"New " + content_name
            new_item = klass.objects.create_obj(
                        sandbox=request.sandbox, name=name )

        # Add new item to this node
        if tree_id:
            tree = BaseItem.objects.active()\
                        .get( request=request, id=tree_id )\
                        .downcast_model
            tree.add_item( new_item )

        return { 'new_item_id': new_item.pk }

    return respond_api_call( request, handler, methods=['POST'] )
