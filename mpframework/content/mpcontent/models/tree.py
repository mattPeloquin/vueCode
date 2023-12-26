#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    TREES === COLLECTIONS
    Trees are hierarchical abstraction that define aggregate collections of content

    Top-level collections are root nodes of trees. They represent discrete
    collections of content, and have special treatment in most UI template views.

    Collections (tree nodes) add additional metadata including information
    for UI template presentation. Tree nodes hold connections to content items
    and participate in a MPTT tree.
      - Sub-nodes are not shared, they belong to one top-level collection.
      - Sub-nodes must be within the sandbox subset of their parent.

    FUTURE - convert tree shared concrete inheritance of baseitem table into virtual
    inheritance to simplify code in several areas and make optimizations easier
"""
from django.db import models
from django.db import transaction
from django.db.models import F
from django.conf import settings
from mptt.models import MPTTModel
from mptt.models import TreeForeignKey

from mpframework.common import log
from mpframework.common import constants as mc
from mpframework.common.tags import tags_Q
from mpframework.common.cache import cache_rv
from mpframework.common.cache import stash_method_rv
from mpframework.common.utils import join_urls
from mpframework.common.utils.strings import comma_tuple
from mpframework.common.model.fields import mpImageField
from mpframework.foundation.tenant.models.sandbox import Sandbox
from mpframework.frontend.sitebuilder.models import TemplateCustom

from .item import BaseItem
from .tree_item import TreeBaseItem
from .tree_manager import TreeManager


class Tree( MPTTModel, BaseItem ):
    """
    Group content into hierarchical tree nodes
    Leverages MPTTModel implementation, which uses the MPTT manager

     - Provides aggregation of items
     - Supports hierarchical creation of content for courses, etc.

    Each node in a tree hierarchy may be associated with:
        - Zero or more BaseItems, optionally grouped by area
        - Children tree nodes
    """

    # Parent is used by MPTT
    parent = TreeForeignKey( 'self', models.SET_NULL,
                blank=True, null=True, related_name='children' )

    # The items attached to this node, excluding children
    items = models.ManyToManyField( BaseItem, blank=True, related_name='tree_nodes',
                through=TreeBaseItem, through_fields=( 'tree', 'item' ),
                symmetrical=False )

    # Tag matching to automatically add content on each save
    _items_tags = models.CharField( db_index=True, db_column='items_tags',
                max_length=mc.CHAR_LEN_UI_CODE, blank=True,
                verbose_name=u"Items tag" )

    # Override templates for the collection
    panel = models.ForeignKey( TemplateCustom, models.SET_NULL,
                related_name='+', blank=True, null=True )
    viewer = models.ForeignKey( TemplateCustom, models.SET_NULL,
                related_name='+', blank=True, null=True )
    nav_template = models.ForeignKey( TemplateCustom, models.SET_NULL,
                related_name='+', blank=True, null=True )
    node_template = models.ForeignKey( TemplateCustom, models.SET_NULL,
                related_name='+', blank=True, null=True )

    # Additional site builder image support
    background_image = mpImageField( blank=True, null=True )
    image3 = mpImageField( blank=True, null=True )
    image4 = mpImageField( blank=True, null=True )

    class Meta:
        verbose_name = u"Collections"

    class MPTTMeta:
        # Aliases for mptt values
        tree_id_attr = 'mptt_id'        # Which tree this is part of
        level_attr = 'mptt_level'       # Level in the tree
        left_attr = 'mptt_left'         # Preorder left count
        right_attr = 'mptt_right'       # Preorder right count

    objects = TreeManager()

    def save( self, *args, **kwargs ):
        """
        To support timewin caching, save the root tree node when a
        node is saved, to ensure changes show in deltas.
        """
        save_top = kwargs.pop( 'save_top', True )
        self.add_items( skip_save=True )
        super().save( *args, **kwargs )
        if save_top and not self.is_top:
            self.my_top.save()

    def _can_complete_Tree( self ):
        # DOWNCAST METHOD
        return True

    def __str__( self ):
        if self.dev_mode:
            return "{}({}l{}p{})-{}".format( self.tag, self.pk, self.mptt_level,
                                              self._provider_id, self.name )
        return super().__str__()

    def clone( self, **kwargs ):
        """
        Leave mptt stuff out of cloning, and rebuild after
        """
        kwargs['_excludes_'] = [ 'parent', 'mptt_id', 'mptt_level',
                                 'mptt_left', 'mptt_right' ]
        return super().clone( **kwargs )

    @transaction.atomic
    def clone_fixup( self, template_sandbox ):
        """
        Add tree and content relationships after content items are cloned
        This can be expensive due to updates on every tree, so manage sizes.
        HACK - Cloning matches content based on name and tags;
        THE NAME/TAG COMBO OF ITEMS MUST BE UNIQUE TO WORK!
        """
        log.debug("Tree clone fixup: %s -> %s", template_sandbox, self)

        # Get tree node to clone
        template = Tree.objects.get( sandbox=template_sandbox,
                                     tag=self.tag, _name=self._name )
        # Setup parent relationship
        if template.parent:
            parent = Tree.objects.get( _provider=self._provider,
                                       tag=template.parent.tag,
                                       _name=template.parent._name )
            self.parent = parent

        # Add items for the tree node
        for item in template.items.filter( sandbox=template_sandbox ).iterator():
            try:
                my_item = BaseItem.objects.get( _provider=self._provider,
                                                tag=item.tag, _name=item._name )
                self.add_item( my_item )
            except BaseItem.DoesNotExist:
                if settings.MP_DEV_EXCEPTION:
                    raise
                log.warning("CLONE tree item missing: %s -> %s", self, item)

        # Save and rebuild tree
        self.save( invalidate=True )

    @property
    def items_tags( self ):
        return comma_tuple( self._items_tags )

    def add_item( self, item, **kwargs ):
        """
        Add existing content item to this tree node's tree items if it isn't
        already and they share at least one sandbox.
        Area can be specified in kwargs, defaults to Core.
        """
        log.debug("Adding to tree node: %s -> %s, %s", self.name, item.name, kwargs)
        node_item = TreeBaseItem.objects.get_quiet( tree=self, item=item,
                    area=kwargs.get( 'area', 'C' ) )
        if not node_item:
            skip_save = kwargs.pop( 'skip_save', False )
            if set( self.sandboxes.all() ).union( set(item.sandboxes.all()) ):
                node_item = TreeBaseItem.objects.create(
                            tree=self, item=item, **kwargs )
                if not skip_save:
                    self.save()
        return node_item

    def add_items( self, skip_save ):
        """
        If tree has items_tags set, add any items to core content that are
        not already present.
        """
        if self.items_tags:
            potential_items = BaseItem.objects.filter_items(
                    tags_Q( self.items_tags ),
                    _provider=self._provider, sandboxes__in=self.sandbox_ids )
            item_ids = self.item_ids( area='C' )
            for item in potential_items.iterator():
                if item.id not in item_ids:
                    self.add_item( item, skip_save=True )
            if not skip_save:
                self.save()

    def update_children( self ):
        """
        Collection sandbox and workflow visibility is special, since collection
        nodes are not sharable, descendants under a node must be within the subset
        of sandboxes and cannot have more permissive workflow.
        """
        log.debug("Update tree node children: %s", self)

        # Fix up all descendents in one loop
        for child in self.get_descendants().iterator():
            child_sandboxes = set( child.sandboxes.all().values_list( 'id', flat=True ) )

            # Remove any sandbox in child not in parent
            child_extra = child_sandboxes - self.sandbox_ids
            for id in child_extra:
                log.debug("Removing node sandbox not in parent: %s -> %s", child, id)
                child.sandboxes.through.objects.filter(
                        baseitem_id=child.pk, sandbox_id=id,
                        ).delete()

            # Add parent sandbox not in child
            child_missing = self.sandbox_ids - child_sandboxes
            for id in child_missing:
                log.debug("Adding node sandbox due to parent: %s -> %s", child, id)
                child.sandboxes.through.objects.create(
                        baseitem_id=child.pk, sandbox_id=id,
                        )

            # Adjust child workflow if more permissive
            if child.workflow_higher( self.workflow ):
                log.debug("Downgrade child workflow under parent: %s -> %s", child, child.workflow)
                child.workflow = self.workflow
                child.save()

    @property
    def is_top( self ):
        return self.is_root_node()

    @property
    @stash_method_rv
    def my_top( self ):
        return self.get_root()

    @property
    def slug( self ):
        """
        Override the default slug to include parents path
        """
        rv = super().slug
        if self.parent:
            rv = join_urls( self.parent.slug, rv )
        return rv

    @property
    def node_slug( self ):
        """
        Keep per-node slug for lookups and page displays
        """
        return super().slug

    @property
    @stash_method_rv
    def background_image_url(self):
        return self.background_image.url if self.background_image else ''
    @property
    @stash_method_rv
    def image3_url(self):
        return self.image3.url if self.image3 else ''
    @property
    @stash_method_rv
    def image4_url(self):
        return self.image4.url if self.image4 else ''

    """-------------------------------------------------------------------
        Tree content

        For MTM content relationships support getting all items or filtered
        by content type and user workflow in as few DB operations as possible.
    """

    def item_ids( self, area=None ):
        """
        Optimized return of ID set for immediate content items.
        """
        opts = { 'tree_id': self.id }
        if area:
            opts['area'] = area
        rv = set( TreeBaseItem.objects.filter( **opts )\
                    .values_list( 'id', flat=True ) )
        return rv

    @property
    def get_children_ids( self ):
        """
        Optimized return of ID list for all immediate children.
        Returns all children ids, regardless of workflow.
        A sanity check for provider is added in case mptt trees
        have a data error regarding parents.
        """
        children = super(Tree,self).get_children()\
                    .filter( _provider=self.provider )\
                    .values_list( 'id', flat=True )
        return list( children )
    @property
    def get_descendant_ids( self ):
        """
        Optimized return of ID list for all children.
        """
        descendants = super(Tree,self).get_descendants()\
                    .filter( _provider=self.provider )\
                    .values_list( 'id', flat=True )
        return list( descendants )

    def _tree_keyfn( self, **kwargs ):
        """
        Return cache key and group for internal tree nodes
        """
        key = [ 'tree', str(self.pk) ]

        # For model caching, use model name
        model = kwargs.get('model')
        model and key.extend([ '_', model.__name__ ])

        # If user filter passed in, convert to sandbox groups
        user = kwargs.get('user')
        user and key.extend([ '_s', str(user._sandbox_id) ])

        key = ''.join( key )
        group = self.cache_group
        log.cache2("CACHE KEY tree, group: %s, key: %s", group, key)
        return key, group

    @cache_rv( keyfn=_tree_keyfn )
    def all_node_items( self, **kwargs ):
        """
        Return queryset of items tied to the node, optionally downcasted to
        a model type and/or filtered for whether required or user has access
        """
        log.debug_on() and log.detail3("TREE all_node_items: %s -> %s", self, kwargs)

        model = kwargs.get('model')
        if model:
            rv = model.objects.mpusing('read_replica')\
                    .filter( tree_bi_nodes__tree=self )\
                    .select_related('baseitem_ptr')
        else:
            rv = BaseItem.objects.mpusing('read_replica')\
                    .filter( tree_bi_nodes__tree=self )

        # Either filter based on required or add it to the queryset
        required = kwargs.get('required')
        if required is None:
            rv = rv.annotate( required=F('tree_bi_nodes__is_required') )
        else:
            rv = rv.filter( tree_bi_nodes__is_required=required )

        user = kwargs.get('user')
        if user:
            rv = rv.filter( user_filter=user )

        return rv

    @cache_rv( keyfn=_tree_keyfn )
    def all_items( self, include_nodes=True, **kwargs ):
        """
        Gets a flat list of all collection sub nodes and content items from this point down,
        optionally filtered by content model type and user access
        """
        log.debug_on() and log.detail3("TREE all_items: %s -> %s", self, kwargs)
        rv = []
        for node in self.get_descendants( include_self=True ).iterator():
            # Add tree node itself to items if no model filtering
            if include_nodes and not kwargs.get('model'):
                rv.append( node )
            # Add the items for the node
            rv.extend( list( node.all_node_items( **kwargs ) ))
        return rv

    #-------------------------------------------------------------------

    def set_workflow( self, level ):
        """
        Update this tree and everything contained by it to have the workflow_level
        Returns the items that were updated
        """
        rv = []
        self.workflow = level

        # Modify each item, but save group invalidation until end
        for item in self.all_items():
            log.debug2("Setting workflow for: %s", item.name)
            item.workflow = level
            item.save( invalidate=False )
            rv.append( item )

        # Invalidate tree and group
        self.save()
        return rv

    def set_sandboxes( self, sandbox_ids ):
        """
        Set sandboxes for this node and everything underneath it
        """
        sandboxes = list( Sandbox.objects.filter( id__in=sandbox_ids ) )

        def _sandbox_update( item ):
            log.debug2("Setting sandboxes for: %s -> %s", item.name, sandboxes)
            item.sandboxes.clear()
            item.sandboxes.add( *sandboxes )
            item.save()

        _sandbox_update( self )
        items = self.all_items()
        for item in items:
            _sandbox_update( item )

        return items
