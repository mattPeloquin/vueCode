#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    VuePortals - Portal, page, and embed frames
    Define entry points for creating portal and link views
    that builds one-page apps from panes.
"""
from django.db import models
from django.conf import settings
from django.db.models import Q
from django.template.defaultfilters import slugify

from mpframework.common import log
from mpframework.common import constants as mc
from mpframework.common.cache import cache_rv
from mpframework.common.model.fields import YamlField
from mpframework.foundation.tenant.models.base import ProviderOptionalModel
from mpframework.foundation.tenant.models import TenantManager

from .theme_mixin import ThemeMixin
from .template import TemplateCustom


class Frame( ProviderOptionalModel, ThemeMixin ):
    """
    Each Frame is endpoint defining structure for pane-based UIs

    Frames require a frame_template that defines how panes are
    constructed into a SPA. Unless completely custom, Frames must
    have at least one pane, and can have multiple.

    Frame sb_options and CSS override Theme (to support holding structural
    options or CSS in place across themes). Other Theme options can be set
    as defaults in Frame, but will be trumpted by Themes.

    The MPF Frame structure YAML is defined below.

        frame_template: frame_template_name.html
        nav_default: Name of home/root screen if more than one pane.
        panes:  (use instead of pane when multiple panes)
            -   (pane1)
                ...(see below)
            -   (pane2)
                ...(see below)
        pane:
            template: Name or path for pane template (required)
            name: UI title for pane (required if more than 1 pane)
            slug: Slug for pane if multiple panes
            items: VM injection for items (default depends on template)
            collections: VM injection name (usually defaults to 'all_tops')
            panel: Force template for collection pages
            nav_home: Custom name of pane's home tab
            options:
                # Read with mpp.pane_options
                # Primary use is to force template overrides of theme AND item defaults
                # to support defining specific layouts (e.g., for collection portals)
                panel_template:  Top-level collection dispaly
                nav_template:    Nav items for child nodes
                node_template:   How child nodes are displayed
                item_template:   Items display as children, or in item portals
            sb_options:
                xyz: OVERRIDE site/frame/theme/skin/item SB option
                ...

    Pane context variables are built into MPF portal structure templates
    and can also be set in templates with data-pane_sb_options,
    but sb_options provided here will trump those.
    """

    # Name the frame is referred to in UI and script name used in templates,
    # config defaults, etc. Script name defaults to name if blank
    name = models.CharField( db_index=True, max_length = mc.CHAR_LEN_UI_DEFAULT )
    _script_name = models.CharField( db_index=True, blank=True,
                max_length=mc.CHAR_LEN_UI_CODE, db_column='script_name' )

    # Filtering for frame purpose
    FRAME_STAFF = (
        ('P', u"Site portal"),
        ('C', u"Collection portal"),
        ('I', u"Item portal"),
        )
    FRAME_HIDDEN = (
        ('K', u"DEV Portal"),
        )
    FRAME_ALL = FRAME_STAFF + FRAME_HIDDEN
    frame_type = models.CharField( max_length=1, choices=FRAME_ALL, default='P',
                verbose_name=u"Type" )

    # Configurable structure, as described above
    structure = YamlField( null=True, blank=True )

    # Optional simplification - pick a single pane for basic frame view
    simple_pane = models.ForeignKey( TemplateCustom, models.SET_NULL, related_name='+',
                blank=True, null=True, verbose_name=u"Simple pane" )

    # Level for access in select boxes
    staff_level = models.IntegerField( choices=TemplateCustom.TEMPLATE_LEVELS,
                blank=True, null=True )

    # Staff notes used in admin
    notes = models.CharField( max_length=mc.CHAR_LEN_DB_SEARCH, blank=True )

    class Meta:
        verbose_name = u"VuePortal"

    objects = TenantManager()
    lookup_fields = ( 'name', '_script_name' )

    def __str__( self ):
        if self.dev_mode:
            return "f({},p{}){}".format( self.pk, self.provider_optional_id, self.name )
        return self.name

    @staticmethod
    def has_access_Q( level ):
        if level:
            return Q( staff_level__isnull=True ) | Q( staff_level__lte=level )
        else:
            return Q( staff_level__isnull=True )

    @property
    def script_name( self ):
        return self._script_name or self.name

    @property
    def slug_name( self ):
        return self._script_name or slugify( self.name )

    @cache_rv( cache='template',
            keyfn=lambda _, skin:( skin.cache_key, skin.sandbox.cache_group ) )
    def structure_context( self, _skin ):
        """
        Returns a dict that will update template context.
        Tied to skin cache key to force invalidation when changes are made.

        Since some frames expect 1 pane, some expect a list, and some
        can use both, provide both a single pane and list.
        """
        rv = {
            'frame_template': self.structure.get( 'frame_template', 'default.html' ),
            'nav_default': self.structure.get( 'nav_default', '' ),
            }

        # Simple pane allows one pane with defaults to be set
        main_pane = {}
        simple_pane = self.simple_pane and self.simple_pane.script_name
        if simple_pane:
            main_pane['template'] = simple_pane

        # Setup list of panes either from one pane or list provided
        main_pane.update( self.structure.get('pane') )
        panes = self.structure.get('panes', [])
        if not ( main_pane or panes ):
            log.info("CONFIG - Frame with no panes: %s", self)
            return rv
        if main_pane:
            panes = [ main_pane ]

        log.debug2("Setting up panes context: %s -> %s", self, panes)
        pane_list = []
        for pv in panes:
            try:
                slug = pv.get('slug') or slugify( pv.get('name') )
                pane_values = {
                    'template': pv.pop('template'),
                    'name': pv.get('name'),
                    'slug': slug,
                    'address': slug,
                    # Override Django call to Python dict members if not present
                    'items': '',
                    }

                # Place remaining values under pane yaml into pane namespace
                pane_values.update( pv )
                pane_list.append( pane_values )

            except Exception as e:
                log.info("CONFIG - Bad Frame Pane: %s %s -> %s", pv, self, e)
                if settings.MP_DEV_EXCEPTION:
                    raise

        rv.update({
            'pane': pane_list[0],
            'panes': pane_list,
            })
        log.debug2("Current frame context: %s", rv)
        return rv
