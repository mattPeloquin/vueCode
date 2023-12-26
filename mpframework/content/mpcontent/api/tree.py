#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Tree content API
"""
import json

from mpframework.common import log
from mpframework.common.api import respond_api_call
from mpframework.common.view import staff_required
from mpframework.common.view import root_only
from mpframework.common.events import sandbox_event

from ..models import Tree
from ..models import BaseItem
from ._utils import item_results


@staff_required
def tree_set_workflow( request ):
    """
    Sets workflow for tree items to the same workflow as the tree
    """
    def handler( payload ):
        tree_id = payload['tree_id']
        level = payload['workflow_level']
        log.info2("API SET TREE Workflow: %s, %s -> %s", request.mpipname, tree_id, level)

        tree = BaseItem.objects.get( request=request, id=tree_id ).downcast_model
        items = tree.set_workflow( level )

        sandbox_event( request.user, 'content_collection_workflow',
                      tree.name, tree.get_workflow_display(), len(items))
        return item_results( items )

    return respond_api_call( request, handler, methods=['POST'] )

@staff_required
def tree_set_sandboxes( request ):
    """
    Adds a tree's sandboxes to all items in the tree
    """
    def handler( payload ):
        tree_id = payload['tree_id']
        sandbox_ids = json.loads( payload.get('sandbox_ids') )
        log.info2("API SET TREE Sandboxes: %s, %s -> %s", request.mpipname, tree_id, sandbox_ids)

        tree = BaseItem.objects.get( _provider=request.user.provider,
                                        id=tree_id ).downcast_model
        items = tree.set_sandboxes( sandbox_ids )

        sandbox_event( request.user, 'content_collection_sites',
                      tree.name, len(items))
        return item_results( items )

    return respond_api_call( request, handler, methods=['POST'] )

@root_only
def tree_rebuild( request ):
    """
    Rebuild corrupted MPTT fields
    """
    def handler( payload ):
        user = request.user
        log.debug("API REBUILD TREE: %s -> %s", user, payload)

        success = Tree.objects.rebuild_from_top( user, payload['tree_top_id'] )

        return { 'rebuilt': success }

    return respond_api_call( request, handler, methods=['POST'] )
