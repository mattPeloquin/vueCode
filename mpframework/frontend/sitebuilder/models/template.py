#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Custom templates (imported with mp_include tag)

    Customer UI is built from using HTML fragments designed to be overridden
    and customized with DB content. This allows for:
     - A base set of UI Legos for Portal, Viewer, Login, etc.
     - Easy Provider customization of UI templates via SiteBuilder
     - AND the creation of completely new UIs

    Names requested by mp_include are processed as:

        Sandbox get_template() -> TemplateCustomManager get_custom()

        1) Any names registered to provider are checked, optionally they
           may be matched to specific sandboxes.
        2) Next any framework/system provider_optional items with the name
           are checked in the DB.
        3) The template value is either taken from the DB content, or
           read from the orig_path location.

    All MPF mp_include templates are in the DB with orig_path references to
    template files STORED IN REVISION CONTROL.
    Templates imported with mp_include tag reference the DB name instead
    of template file path.

    User workflow is also considered, to allow a simple dev/prod publishing
    system with a backup. This supports experimenting with template code on
    live sites without creating copies of every sandbox.
"""
from django.db import models
from django.db.models import Q
from django.conf import settings
from django.db.utils import OperationalError
from django.template.loader import get_template
from django.template.defaultfilters import slugify

from mpframework.common import log
from mpframework.common import constants as mc
from mpframework.common.cache.stash import stash_method_rv
from mpframework.foundation.tenant.models.base import ProviderOptionalModel

from .template_manager import TemplateCustomManager


class TemplateCustom( ProviderOptionalModel ):
    """
    Containers for "Lego" fragments of Django/KO/HTML templates
    Any templates used via {% mp_include %} tags is processed here
    """

    # Name the template is referred to in UI and script name used in templates,
    # config defaults, etc. script_name defaults to name if blank
    name = models.CharField( db_index=True, max_length=mc.CHAR_LEN_UI_DEFAULT )
    _script_name = models.CharField( db_index=True, blank=True,
                max_length=mc.CHAR_LEN_UI_CODE, db_column='script_name',
                verbose_name=u"Script name" )

    # Path to MPF code, if template is representing or overriding an MPF file
    orig_path = models.CharField( db_index=True, blank=True,
                max_length=mc.CHAR_LEN_UI_DEFAULT )

    # Support basic publish/backout workflow for custom templates
    code_prod = models.TextField( blank=True )
    code_dev = models.TextField( blank=True )
    code_backup = models.TextField( blank=True )

    # Filtering for displaying template selections in the UI
    # HACK FUTURE - original 1 letter code was convenient for array lookups, but has
    # become unwieldy due to number of template types
    TEMPLATE_CUSTOM = tuple(sorted((
        # Selectable panes
        ('P', u"Portal pane"),      # Panes used in main VuePortal frames
        ('G', u"Collection pane"),  # Individual collection pane
        ('H', u"Item pane"),        # Individual item pane
        # Selectable theme elements
        ('A', u"Font"),
        ('B', u"Style"),
        ('C', u"Color"),
        ('D', u"Style mixin"),      # Global style add-in
        ('F', u"Viewer"),           # Injected viewer templates
        ('I', u"Item layout"),      # Layout for non-tree content items
        ('N', u"Nav layout"),       # Nav element layout
        ('Q', u"Collection page"),  # Tree-top display panels
        ('R', u"Collection node"),  # Tree-node display panels
        ('L', u"Login page"),
        # Other templates types organized for admin
        ('E', u"Customer emails"),  # Default email templates for customers
        ('V', u"Custom AddIn"),     # Customer template includes
        ('U', u"Landing page"),     # Separate landing pages
        ('T', u"Portal pieces"),    # Easy mod client snippets/templates
        ('W', u"Portal structure"), # Portal templates not usually modified
        ('Y', u"Platform client"),  # Internal non-portal client templates
        ('Z', u"Platform"),         # Internal non-portal
        ), key=lambda t: t[1] ))
    TEMPLATE_HIDDEN = (
        ('J', u"DEV client inject"),
        ('K', u"DEV"),
        )
    TEMPLATE_ALL = TEMPLATE_CUSTOM + TEMPLATE_HIDDEN
    # Client templates injected into loads
    PLATFORM_TEMPLATES = 'JY'
    PORTAL_TEMPLATES = 'FINQRT'

    template_type = models.CharField( max_length=1, choices=TEMPLATE_ALL,
                verbose_name=u"Type" )

    # Identify sandboxes to apply NON-SYSTEM templates to
    _all_sandboxes = models.BooleanField( default=True, db_column='all_sandboxes',
                verbose_name=u"All site" )
    _sandboxes = models.ManyToManyField( 'tenant.Sandbox', blank=True,
                related_name='templates' )

    # Use staff level to hide templates as options in the UI
    # This DOES NOT impact use of configured templates, only select visibility
    TEMPLATE_LEVELS = (
        ( None, u"Everyone can see" ),
        ( mc.STAFF_LEVEL_LOW, u"EasyVue staff" ),
        ( mc.STAFF_LEVEL_MED, u"BizVue staff" ),
        ( mc.STAFF_LEVEL_HIGH, u"SiteBuilder" ),
        ( mc.STAFF_LEVEL_ALL, u"SiteBuilder Pro" ),
        ( mc.STAFF_LEVEL_ROOT, u"ROOT staff" ),
        )
    staff_level = models.IntegerField( choices=TEMPLATE_LEVELS,
                blank=True, null=True )

    notes = models.CharField( max_length=mc.CHAR_LEN_DB_SEARCH, blank=True )

    class Meta:
        verbose_name = u"Custom template"

    objects = TemplateCustomManager()
    lookup_fields = ( 'name', '_script_name' )

    def __str__( self ):
        if self.dev_mode:
            return "tc({},p:{}){}".format( self.pk, self.provider_optional_id,
                    self.name )
        return self.name

    @staticmethod
    def has_access_Q( level ):
        if level:
            return Q( staff_level__isnull=True ) | Q( staff_level__lte=level )
        else:
            return Q( staff_level__isnull=True )

    def has_access( self, level ):
        return self.staff_level <= level

    def template_code( self, dev=False ):
        """
        Provides code based on workflow, with reversion to any on-disk
        template if present, blank if nothing found
        """
        rv = ''
        if dev and self.code_dev:
            rv = self.code_dev
        elif self.code_prod:
            rv = self.code_prod
        elif self.orig_path:
            rv = self.orig_code
        return rv

    @property
    def script_name( self ):
        return self._script_name or self.name

    @property
    def slug_name( self ):
        return self._script_name or slugify( self.name )

    @property
    @stash_method_rv
    def orig_code( self ):
        """
        Get an original code file, if any
        Swallow any problems so one template config issue doesn't kill all loading
        """
        rv = ''
        if self.orig_path:
            try:
                template = get_template( self.orig_path )
                rv = template.template.source
            except OperationalError:
                # Most likely DB connection needs reset, let caller manage
                raise
            except Exception as e:
                if settings.MP_DEV_EXCEPTION:
                    raise
                log.warning("CONFIG - Problem loading orig code: %s -> %s", self, e)
        return rv

    @property
    def all_sandboxes( self ):
        """
        Sandbox selection is only applicable to non-system items
        """
        return self.is_system or self._all_sandboxes

    @property
    @stash_method_rv
    def sandboxes( self ):
        if not self.all_sandboxes:
            return list( self._sandboxes.all() )

    def publish( self ):
        """
        FUTURE - Add publishing to move dev into custom, with backup
        """
        pass
