#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Concrete base class for all content items and collections
"""
from django.db import models
from django.urls import reverse

from mpframework.common import log
from mpframework.common import constants as mc
from mpframework.common.tags import validate_item_tag
from mpframework.common.utils import now
from mpframework.common.cache import stash_method_rv
from mpframework.common.cache import invalidate_cache_group
from mpframework.common.model.fields import mpDateTimeField
from mpframework.common.model.concrete_mixin import ConcreteBaseMixin
from mpframework.frontend.sitebuilder.models import TemplateCustom

from .base.attr import BaseAttr
from .item_manager import ItemManager


class BaseItem( ConcreteBaseMixin, BaseAttr ):
    """
    BaseItem extends BaseAttr as a concrete base for all content items and trees;
    one base table holds all shared info for both items and trees.

    All attributes of BaseItem are used in content items.
    A small number are NOT used by Trees/collections; this isn't perfect, but
    simplifies sharing of common traits with the shared BaseItem table.

    Content items derive from this base class using multi-table inheritance;
    all items have base info stored in one shared table, while specialized
    info is stored in separate per-item type derived tables.
    BaseItem is normally instantiated in a derived class. Concrete mixin is
    sometimes used to optimize access to base info.

    External public files stored with content items go into the provider
    content folder defined in BaseAttr, while protected files go under
    different folders defined by specialized types.
    """

    # Add index to modified for use with timewin
    hist_modified = mpDateTimeField( db_index=True, default=now,
                verbose_name=u"Modified" )

    # Catalog Tag/Code - text-matching link to catalog
    # Tag is optional for cases such as including content via tree node collections
    # or simple sites with items sold under includes_all products
    tag = models.CharField( db_index=True, validators=[ validate_item_tag ],
                max_length=mc.CHAR_LEN_UI_CODE, blank=True,
                verbose_name=u"License tag" )

    # Optional designation of content as domain item (e.g., "Lesson")
    portal_type = models.ForeignKey( 'mpcontent.PortalType', models.SET_NULL,
                blank=True, null=True, related_name='items',
                verbose_name=u"Portal type" )

    # Optional explicit assignment of content to a portal group
    portal_group = models.ForeignKey( 'mpcontent.PortalGroup', models.SET_NULL,
                blank=True, null=True, related_name='groups',
                verbose_name=u"Portal group" )

    # An item can belong to multiple categories
    # FUTURE - only connections to top-level collections currently exposed
    portal_categories = models.ManyToManyField( 'mpcontent.PortalCategory',
                blank=True )

    # Override the template used to render item (or item_default for trees)
    item_template = models.ForeignKey( TemplateCustom, models.SET_NULL,
                related_name='+', blank=True, null=True )

    # What action should occur when an item is accessed?
    # Some content has no actions, and not all actions make sense for all items,
    # so specializations may modify the choices available.
    ACTION_TYPICAL = (
        ( '', u"Default" ),
        ( 'action_viewer', u"Viewer" ),
        ( 'action_win', u"New tab" ),
        ( 'action_inline', u"Current tab" ),
        )
    _action = models.CharField( max_length=24, blank=True,
                verbose_name=u"Access method" )

    # Optional point in time to indicate the content is relevant
    # The use of this may vary depending on content
    _available = mpDateTimeField( db_index=True, null=True, blank=True,
                db_column='available' )

    """
    Content sizing
    MPF has relative (points) and concrete (size) integer sizing for content.
    'points' relative sizing:
      - Supports usage metering
      - Can be compared and aggregated
      - Defaults to 1 if not set
    'size' concrete sizing:
      - Specializations and options make assumptions about what size represents
        (e.g., length in minutes for videos).
      - Defaults to 0 if not set
    """
    _points = models.IntegerField( blank=True, null=True, db_column='points' )
    size = models.IntegerField( blank=True, null=True )

    # Customizable URL slug that replaces id in urls
    # If this is filled in, the URL will appear in sitemap if in production
    _slug = models.SlugField( db_index=True, allow_unicode=True,
                blank=True, db_column='slug', verbose_name=u"URL slug" )

    # Search tags for filtering portal display of content in the portal UI;
    # not indexed since NOT used for DB searching in staff screens
    search_tags = models.CharField( max_length=mc.CHAR_LEN_UI_LONG, blank=True )

    # Text field for staff DB searches and for dispaly in admin and reports;
    # never shown in portal
    internal_tags = models.CharField( db_index=True, blank=True,
                max_length=mc.CHAR_LEN_UI_CODE, verbose_name=u"Internal tags" )

    # Sitebulder auxiliary content, intended for use as snippets of
    # text with special style in templates (e.g., author)
    tooltip = models.CharField( max_length=mc.CHAR_LEN_UI_BLURB, blank=True )
    text3 = models.CharField( max_length=mc.CHAR_LEN_UI_BLURB, blank=True )
    text4 = models.CharField( max_length=mc.CHAR_LEN_UI_BLURB, blank=True )

    # HTML blocks for portal display
    # These are NOT included in search and by default are loaded on demand
    # Exact usage can vary by by template but html1 is intended as description,
    # html2 as a popup/tabbed about, and html3 is shown with content access.
    html1 = models.TextField( blank=True )
    html2 = models.TextField( blank=True )

    # FUTURE - convert to an actual protected link
    html3 = models.TextField( blank=True )

    # Track number of times content (that is served vs. metadata) is updated
    # This is used primarily to invalidate cached content access session URLs
    content_rev = models.IntegerField( default=0 )

    class Meta:
        verbose_name = u"Content item"

    # Specializations define the access type
    access_type = None

    objects = ItemManager()

    select_related = ( 'portal_type', 'portal_group' )
    select_related_admin = select_related

    lookup_fields = ( '_name__icontains', 'id__iexact',
                'internal_tags__icontains', 'tag__icontains' )

    # Name of id for sandbox through table optimizations
    sandbox_through_id = 'baseitem_id'

    # Specializations add names of actual content fields (vs. metadata)
    content_fields = []

    def __init__( self, *args, **kwargs ):
        """
        Implement a dirty flag on tag for invalidation
        """
        super().__init__( *args, **kwargs )
        self._orig_tag = self.tag

    def save( self, *args, **kwargs ):
        """
        Shared save preparations and invalidations
        """
        super().save( *args, **kwargs )

        # If tag is new or changes
        # FUTURE - convert changes on tag to signal from content
        if self._orig_tag != self.tag:

            # Invalidate PRODUCTS in sandboxes dependent on the content
            from mpextend.product.catalog.cache import cache_group_catalog
            for sandbox in self.sandboxes.all():
                invalidate_cache_group( cache_group_catalog( sandbox.pk ) )

            # For non-tree items, check if the item should be added to tree
            if self.tag and not self.is_collection:
                from mpframework.common.tags import tag_match
                from .tree import Tree
                potential_nodes = Tree.objects.filter( _provider=self._provider,
                            sandboxes__in=self.sandbox_ids )\
                            .exclude( _items_tags='' )

                for node in potential_nodes.iterator():
                    if tag_match( self.tag, node.items_tags ):
                        node.add_item( self.downcast_model )

    def _log_instance( self, message ):
        # For large sandboxes, many base item objects are created in bootstrap
        log.debug_on() and log.detail2("%s BaseItem: %s (%s)", message, self.pk, id(self))

    def __str__( self ):
        """
        Include tag in the default string so admin views in complex sandboxes
        can differentiate items in lookups
        """
        rv = str( self.name )
        if self.tag:
            rv = "{} - {}".format( self.tag, rv )
        if self.dev_mode:
            rv = "{}({})".format( rv, self.unique_key,  )
        return rv

    def update_content_rev( self ):
        """
        Reset content revision if all content is empty
        """
        if not any( getattr( self, field, None ) for field in self.content_fields ):
            self.content_rev = 0

    @property
    def dict( self ):
        rv = super().dict
        rv.update({
            'tag': self.tag,
            'name': self.name,
            'tooltip': self.text3,
            'text3': self.text3,
            'text4': self.text4,
            'portal_type': self.portal_type.name if self.portal_type else '',
            'size': self.size,
            'points': self.points,
            'search_tags': self.search_tags,
            })
        return rv

    #--------------------------------------------------------------------

    @property
    def type_db( self ):
        """
        Provides Django db content_type name for programmatic use
        """
        return self.downcast_model_name

    @property
    def is_collection( self ):
        """
        HACK to allow easy seperation of items from collections
        """
        return self.downcast_model_name == 'tree'

    @property
    def type_name( self ):
        """
        Override DB name for display to use verbose_name
        """
        return self.downcast_call('_type_name')
    # DOWNCAST METHOD
    def _type_name( self ):
        return self._meta.verbose_name_raw

    def type_view( self, request=None ):
        """
        Support variations to how the content is accessed/displayed,
        defaults to the type of content (which means no access variations
        within that content type).
        """
        return self.downcast_call('_type_view')
    # DOWNCAST METHOD
    def _type_view( self, request=None ):
        return self.type_db

    @property
    def can_complete( self ):
        """
        May be overridden in sub-types to indicate whether this content
        can be 'completed' or just accessed/viewed/downloaded
        """
        return self.downcast_call('_can_complete')
    # DOWNCAST METHOD
    def _can_complete( self ):
        return False

    @property
    def access_action( self ):
        """
        Content specializations decide how define action; the default
        is to display in the item in the default viewer.
        """
        return self.downcast_call('_access_action')
    # DOWNCAST METHOD
    def _access_action( self ):
        return self._action if self._action else 'action_viewer'

    def get_access_url( self, request, **kwargs ):
        """
        Default response for access calls, creates a protected access
        URL by calling the request handler registered for the content type.
        May only be called on specializations, and may be overridden.
        """
        from ..delivery import create_access_url

        if not self.access_type:
            return
        log.debug("Access url: %s -> %s, %s", request.mpipname, self, kwargs)
        data = kwargs.pop( 'data', self.pk )

        # Support per-item override of delivery mode
        delivery_mode = self.sb_options['access.delivery_mode']
        if delivery_mode:
            kwargs['default_mode'] = delivery_mode

        # Pass the content revision to use in access link for url caching
        # of items that may not use filename mangling
        kwargs['content_rev'] = self.content_rev

        return create_access_url( request, self.access_type, data, **kwargs )

    def access_data( self, request, **kwargs ):
        """
        Specializations can override this to provide a short-cut
        for direct response reuse when appropriate.
        """
        return {
            'default_url': self.get_access_url( request, **kwargs ),
            }

    @property
    def available( self ):
        """
        Overridable start of availability window
        Return None for immediately available, or a datetime that access
        is allowed users in Prod or Beta workflow.
        """
        return self._available

    @property
    def version( self ):
        """
        An optional subtype-specific integer that can represent a key
        to a latest version of the content
        """
        return 0

    @property
    def slug( self ):
        return self._slug or self.tag or str(self.pk)

    @property
    def my_tree_nodes( self ):
        """
        Returns list of TREE OBJECTS for tree nodes this item belongs to
        Expensive due to downcast, so only use when all tree node classes are needed
        """
        return self.my_trees( downcast=True )

    @stash_method_rv
    def my_trees( self, downcast=False ):
        rv = []
        bi_nodes = self.tree_bi_nodes.exclude( tree__workflow__in='R' )
        for bi_node in bi_nodes:
            node = bi_node.tree
            if downcast:
                node = node.downcast_model
            rv.append( node )
        log.detail3("Tree nodes for item: %s -> %s", self, rv)
        return list( set(rv) )

    @stash_method_rv
    def my_tags( self ):
        """
        List of tags associated with this content, which means either
        its own tag or ANY tree's tags that it is underneath.
        """
        tags = [ self.tag ]
        for node in self.my_trees():
            tags.extend( node.my_tags() )
        return list( set([ str( tag ).strip().lower() for tag in tags ]) )

    @property
    def points( self ):
        return self._points if self._points else 1

    @property
    def description( self ):
        """
        Overridable text for display in default descriptions
        like portal and catalog templates
        """
        return self.text1 if self.text1 else str(self)
