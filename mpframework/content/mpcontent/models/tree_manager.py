#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Tree manager
"""
from django.db import transaction
from django.db.models import Max
from mptt.models import TreeManager as mpttTreeManager

from mpframework.common import log
from mpframework.common.events import sandbox_event

from .item_manager import ItemManager
from .item_manager import ItemQuerySet


class TreeQuerySet( ItemQuerySet ):
    """
    Filters specific to trees
    """

    def filter_tops( self, *args, **kwargs ):
        kwargs['parent__isnull'] = True
        return self.filter( *args, **kwargs )


class _TreeManager( mpttTreeManager, ItemManager ):
    """
    Because trees are MPTTModels, need to base the manager
    on MPTT TreeManager and add ContentManager filtering functionality
    """

    def _get_queryset( self ):
        return TreeQuerySet( model=self.model )

    def create_node( self, user, workflow, name, parent=None ):
        """
        Create new roots outside admin
        """
        sandbox_event( user, 'content_collection_new', name )

        # Create new node with the package
        new_node = self.model( provider=user.provider, name=name,
                    workflow=workflow, parent=parent )
        new_node.save()

        # If parent is provided, setup parent relationship and
        # add the child to all sandboxes the parent is part of
        if parent:
            new_node.insert_at( parent, save=True )
            for sandbox in parent.sandboxes:
                new_node.sandboxes.add( sandbox )

        # Otherwise create the node in the current sandbox
        else:
            new_node.sandboxes.add( user.sandbox )

        return new_node

    def get_node( self, user, node ):
        """
        If a node or node ID is passed in, convert to tree node object.
        Raises exception if tree node is not found.
        """
        log.debug("TreeManager get node: %s", node)
        options = { 'pk': int(getattr(node, 'id', node)) }
        if user.sees_sandboxes:
            options['_provider'] = user.provider
        else:
            options['user_filter'] = user
        return self.get( **options )

    @transaction.atomic
    def _get_next_tree_id( self ):
        """
        Override default mptt check for next tree ID to ensure entire table
        across all providers is taken into account.
        FUTURE SCALE - locking all rows to get aggregate eventually won't scale
        """
        qs = self.all_rows().select_for_update()\
                .aggregate( Max(self.tree_id_attr) )
        max_tree_id = list( qs.values() )[0]
        max_tree_id = max_tree_id or 0
        return max_tree_id + 1

    @transaction.atomic
    def rebuild_from_top( self, user, node ):
        """
        Rebuild a broken tree
        MPTT fields are essentially a cache of tree structure and there
        have been operational cases where MPTT fields get out of whack,
        from programming error or failed DB action.
        Since this can effectively make content inaccessible or cause tenancy
        violation, need an easy way for root admin to robustly fix all types
        of tree corruption and at least make tree nodes visible if the
        structure can't be salvaged.
        Always assigns a new tree_id and honors provider_id to resolve cases where
        trees have been crosslinked.
        """
        node = self.get_node( user, node )
        if not node.is_top:
            log.warning("Rebuild tree called on non-root node")
            return
        provider_id = node._provider_id
        log.info("REBUILDING TREE: %s -> %s, %s", user, provider_id, node)

        # Set new tree ID in root - mptt tree will be indeterminate until the
        # new tree is completed with this new id
        # FUTURE SCALE - get_next_tree_id will lock all rows for transaction
        new_tree_id = self._get_next_tree_id()

        def _mp_rebuild_helper( node_id, left=1, level=0 ):
            """
            Based on mptt's rebuild implementation, follow the primary key parent
            relationships into children, and then set left and right from
            the bottom on the way back out.
            """
            right = left + 1
            # Get valid child IDs using PK of the tree node
            child_qs = self._mptt_filter( parent__pk=node_id )
            child_ids = child_qs.values_list( 'pk', flat=True )
            if child_ids:
                log.info("Rebuilding children: %s -> %s", node_id, child_ids)
                for child_id in child_ids:
                    right = _mp_rebuild_helper( child_id, right, level + 1 )
            # Update tree while backing out of children; only include items
            # that are in the trees provider
            node = self.get( pk=node_id )
            good_node = node._provider_id == provider_id
            if good_node:
                node.mptt_id = new_tree_id
                node.mptt_level = level
                node.mptt_left = left
                node.mptt_right = right
                log.info("MPTT child updating: %s -> %s l:%s r:%s lvl: %s",
                            new_tree_id, node_id, left, right, level)
                right += 1
            # If the node is crosslinked from another provider, make it a root
            else:
                log.info("ERROR DATA - Fixing crosslinked MPTT child: %s", node_id)
                node.parent = None
                node.mptt_id = self._get_next_tree_id()
                node.mptt_level = 0
                node.mptt_left = 1
                node.mptt_right = 2
                right -= 1

            # MPTT save normally does not update MPTT info directly, so
            # force update of only the MPTT fields
            fields = ['parent', 'mptt_id', 'mptt_level', 'mptt_left', 'mptt_right']
            node.save( update_fields=fields, save_top=False )

            return right

        # Start walking the tree
        _mp_rebuild_helper( node.pk )

        return True

# Use from_queryset to include both custom manager and queryset methods
TreeManager = _TreeManager.from_queryset( TreeQuerySet )
