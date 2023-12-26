#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Sandboxes are the key abstraction for layered multi-tenancy:

     - segregate usersnames, i.e., users sign-up for sandboxes
     - define URLs, UI theming, and site options
     - selectively expose models with Provider scope (content)
     - define scope for models (licensing)

    From a customer/user perspective, each sandbox looks like
    a different site that they sign up for.
"""
from django.db import models
from django.conf import settings
from django.urls import reverse
from django.template.loader import get_template
from timezone_field import TimeZoneField

from mpframework.common import log
from mpframework.common import sys_options
from mpframework.common import constants as mc
from mpframework.common.model import BaseModel
from mpframework.common.model import CachedModelMixin
from mpframework.common.model.fields import YamlField
from mpframework.common.model.fields import mpFileFieldPublic
from mpframework.common.model.fields import mpImageField
from mpframework.common.template import mpTemplate
from mpframework.common.cache import cache_rv
from mpframework.common.cache import stash_method_rv
from mpframework.common.cache.groups import cache_group_sandbox
from mpframework.common.cache.groups import invalidate_group_sandbox
from mpframework.common.utils import join_urls
from mpframework.common.delivery import DELIVERY_DEFAULT, DELIVERY_MODES
from mpframework.frontend.sitebuilder.models import Theme
from mpframework.frontend.sitebuilder.models.theme_mixin import ThemeMixin
from mpframework.frontend.sitebuilder.models.frame_mixin import FrameSelectMixin

from ..signals import sandbox_change
from .base.tenant_clone import TenantCloneMixin
from .provider import Provider
from .sandbox_manager import SandboxManager

# Load SandboxHost here to ensure it is loaded with test fixtures
from .sandbox_host import SandboxHost


class Sandbox( TenantCloneMixin, ThemeMixin, FrameSelectMixin,
               CachedModelMixin, BaseModel ):
    """
    A Sandbox represents a given hosted instance of a storefront.
    Sandboxes have a one-to-many relationship with SandboxHosts, which
    define the URLs that a sandbox can support.
    Default subdomain for sandbox (valid DNS):
      - Reserves the URL name in the root namespace for the sandbox
      - Must be synched with SandboxHost to provide the default SSL URL
      - Provides an internal textual id / system_name for sandbox
    """
    _provider = models.ForeignKey( Provider, models.CASCADE,
                related_name='my_sandboxes', db_column='provider_id' )
    subdomain = models.CharField( unique=True, max_length=mc.CHAR_LEN_UI_CODE )

    # Public name of sandbox
    name = models.CharField( max_length=mc.CHAR_LEN_UI_LINE )

    # Timezone for displaying time information
    timezone = TimeZoneField( default='UTC',
                choices=[ (t[0], t[1]) for t in settings.MP_TIME_ZONES ] )

    # TO Email for sending system notifications to sandbox staff
    # Also considered main contact email for site owner
    # Instead of supporting multiple, assume they can setup alias if needed
    _email_staff = models.EmailField( max_length=mc.CHAR_LEN_UI_EMAIL, blank=True,
                db_column='email_staff' )

    # FROM email for sending to users
    # NOTE - this must be registered in AWS SES to work
    email_support = models.EmailField( max_length=mc.CHAR_LEN_UI_EMAIL )

    # Default sandbox theme
    theme = models.ForeignKey( Theme, models.SET_NULL, null=True, blank=True,
                related_name='sandboxes_in_use' )

    # Hidden site options, never seen by staff or users
    # These can be site specific, or override provider policy settings,
    # and in some cases system settings (e.g., feature flags)
    _policy = YamlField( null=True, blank=True, db_column='policy' )

    # Configurable sandbox options, seen by expert users
    options = YamlField( null=True, blank=True )

    """
    User adjustable balance of delivery security/compatibility

    These users settings balance compatibility for different user scenarios
    (firewall issues, etc.) with protection level, scalability, and use of
    global Cloud front endpoints.
    These are mapped on to various internal settings to provide multiple
    delivery approaches.

    These settings can be overridden by per-user compatibility settings and
    more specific settings in sandbox options.
    """
    delivery_mode = models.CharField( max_length=16, choices=DELIVERY_MODES,
                default=DELIVERY_DEFAULT )

    # Types of events to send to the staff email
    NOTIFY_LEVEL = (
        ( -1, u"No notifications" ),
        ( 0, u"Sign-ups" ),
        ( 10, u"New licenses" ),
        ( 20, u"Major staff actions" ),
        ( 30, u"Minor staff actions" ),
        ( 40, u"Badge completion" ),
        ( 50, u"Collection completion" ),
        ( 60, u"Item completion" ),
        ( 70, u"User content access" ),
        ( 80, u"Visitor content access" ),
        ( 100, u"All events" ),
        )
    notify_level = models.IntegerField( choices=NOTIFY_LEVEL, default=0 )

    # Resource path (no spaces, valid path)
    # Used for some S3 folders and name stamping under the provider
    # Defaults to subdomain if blank
    # MUST KEEP SYNCED WITH S3 FOLDER DEPENDENCIES
    _resource_path = models.CharField( blank=True,
                max_length=mc.CHAR_LEN_UI_LONG, db_column='resource_path' )

    # Content customization
    # Both standardized values and blocks for sandbox-wide reuse
    icon = mpImageField( blank=True, null=True,
                mpoptions={ 'img_class': 'es_image_med_fixed' } )
    logo = mpImageField( blank=True, null=True )
    hero_image = mpImageField( blank=True, null=True,
                db_column='banner_image' ) # TBD NOW DB
    hero_video = mpFileFieldPublic( direct=True, mpfile=False, blank=True )
    hero_image2 = mpImageField( blank=True, null=True )
    summary = models.CharField( max_length=mc.CHAR_LEN_UI_BLURB, blank=True )
    intro_html = models.TextField( max_length=mc.TEXT_LEN_MED, blank=True )
    home_html = models.TextField( max_length=mc.TEXT_LEN_MED, blank=True )
    login_html = models.TextField( max_length=mc.TEXT_LEN_MED, blank=True )
    footer_html = models.TextField( max_length=mc.TEXT_LEN_MED, blank=True )
    terms_html = models.TextField( max_length=mc.TEXT_LEN_LARGE, blank=True )
    html1 = models.TextField( max_length=mc.TEXT_LEN_MED, blank=True )
    html2 = models.TextField( max_length=mc.TEXT_LEN_MED, blank=True )

    # Tax entries are configured by postal code and must be assigned to a sandbox
    taxes = YamlField( null=True, blank=True )

    # HTML blocks to add scripting to all pages (in addition to theme values)
    snippet_head = models.TextField( max_length=mc.TEXT_LEN_MED, blank=True )
    snippet_body = models.TextField( max_length=mc.TEXT_LEN_MED, blank=True )

    notes = models.CharField( max_length=mc.CHAR_LEN_DB_SEARCH, blank=True )

    class Meta:
        verbose_name = u"Site"
        verbose_name_plural = u"Sites"

    # Get portal objects for option overrides
    select_related = ( '_provider' ,)

    objects = SandboxManager()
    provider_staff_sees_sandboxes = True
    _tenancy_type = '_provider'

    def __init__( self, *args, **kwargs ):
        """
        Sandbox objects are normally cached immediately upon initial request
        creation, so no state should be set.
        """
        super().__init__( *args, **kwargs )

    def __str__( self ):
        if self.dev_mode:
            return "{} s{}p{}_{} ({})".format( self.name, self.pk, self._provider_id,
                                                self.subdomain, id(self) )
        return self.name

    def _log_instance( self, message ):
        log.debug_on() and log.detail("%s Sandbox: %s", message, self)

    def save( self, *args, **kwargs ):
        super().save( *args, **kwargs )
        sandbox_change.send( sender=self.pk )

        # HACK - invalidate system options if root sandbox is modified
        if self.is_root:
            sys_options.invalidate_all()

    """
    SANDBOX CACHING
    Sandbox instances use default cache group, 'tg' and are chained upstream
    to provider and system for invalidation.

    However, cache_group is stashed for the life of the object, which will
    prevent a sandbox object from changing in its lifetime from external
    invalidation - usually for a request/response or task execution.

    Distributed caching of sandboxes is handled by get_sandbox through url.
    Stashing is used on processed values, so most methods don't do their
    own caching of return values across processes (except hosts and templates).

    FUTURE - could break up sandbox namespace to add template or others
    to limit the scope of invalidation on system changes.
    """
    @property
    @stash_method_rv
    def cache_group( self ):
        return cache_group_sandbox( self.pk, self._provider_id, system=True )

    def invalidate_group( self ):
        invalidate_group_sandbox( self.pk )
        invalidate_group_sandbox( self.pk, self._provider_id )

    @property
    @stash_method_rv
    def policy( self ):
        """
        Sandbox policy includes and overrides provider
        """
        rv = self.provider.policy
        rv.update( self._policy )
        return rv

    #-------------------------------------------------------------------

    @property
    def is_root( self ):
        """
        HACK - root sandbox is hard-coded as the first sandbox
        """
        return self.pk == settings.MP_ROOT['SANDBOX_ID']

    @property
    def provider( self ):
        return self._provider

    @property
    def resource_path( self ):
        return self._resource_path if self._resource_path else self.subdomain

    @property
    def public_storage_path( self ):
        # Sandbox public files live together
        return self.policy.get( 'storage.sandbox_public',
                    join_urls( self.provider.public_storage_path, self.resource_path ) )

    @property
    def media_url( self ):
        # Full URL to public resource/upload folder
        return join_urls( settings.MEDIA_URL, self.public_storage_path )

    @property
    def language_code( self ):
        """
        FUTURE - eventually support sandbox i18n based on DB and/or string files
        """
        return settings.LANGUAGE_CODE

    #-------------------------------------------------------------------
    # Presentation customization

    def _template_keyfn( self, path, use_dev=False, option=None,
                            template_type=None ):
        key = '-'.join([ str(path), 'use_dev' if use_dev else '',
                         option if option else '',
                         template_type if template_type else '' ])
        return key, self.cache_group

    @cache_rv( keyfn=_template_keyfn, cache='template' )
    def get_template( self, path, use_dev=False, option=None, template_type=None ):
        """
        Called for all mp_include tags and some backend code.
        Load templates (from DB or file) and cache contents for the sandbox,
        taking into account any custom or dev workflow overrides.
        Returns an mpTemplate object if successful.
        Custom templates are tried at the sandbox, provider, and then system level,
        using name (and path for overrides).
        """
        from mpframework.frontend.sitebuilder.models import TemplateCustom
        try:
            template_code = None

            custom = TemplateCustom.objects.get_custom( path, self, template_type )

            if custom:
                log.debug2("CustomTemplate: dev:%s, %s, %s", use_dev, path, option)
                template_code = custom.template_code( use_dev )
            else:
                log.debug2("Django template: %s, %s", path, option)
                # Django template caching is on, so although each Django template load
                # checks all app template locations in all platforms, it only happens
                # once per process per template file
                template = get_template( path )
                template_code = template.template.source

            return mpTemplate( template_code, option )

        except Exception as e:
            if settings.MP_TEMPLATE_DEBUG or settings.MP_TESTING:
                log.exception("Sandbox get_template: %s -> %s", self, path)
                raise
            log.warning("CONFIG - bad template: %s, %s -> %s", self, path, e)

    #-------------------------------------------------------------------
    # Host URL support

    @cache_rv( group='cache_group' )
    def get_host( self, **kwargs ):
        """
        Return SandboxHost that meets criteria, return first of multiple
        """
        hosts = list( self.hosts.filter( **kwargs ) )
        return hosts[0] if hosts else None

    def host_url( self, path=None, host=None, force_ssl=False ):
        """
        Return host URL ready for use in templates and redirects with
        scheme and host name based on Sandbox host settings.
        If force_ssl is set, only https hosts will be returned.
        Allows redirection back and forth between HTTP and HTTPS addresses
        such as http://xyz.com and https://xyz.vueocity.com
        """
        host = host or self.main_host
        log.detail2("Getting sandbox host url: %s -> %s ssl(%s)",
                    self, host, force_ssl)
        if host:
            host_name = host.host_name
        else:
            log.info2("Sandbox missing host, using subdomain: %s", self)
            host_name = '{}.{}'.format(
                        self.subdomain, settings.MP_ROOT['HOST'] )

        scheme = 'http' if (host and not host.https) and not force_ssl else 'https'
        rv = '{}://{}'.format( scheme, host_name )

        if path:
            rv = '{}{}'.format( rv, path )

        log.debug2("Sandbox host url: %s -> %s", self, rv)
        return rv

    @property
    def main_host( self ):
        return self.get_host( main=True )

    @property
    def main_host_url( self ):
        return self.host_url()

    @property
    def main_host_ssl( self ):
        return self.host_url( force_ssl=True )

    def portal_url( self, ename=None, evalue=None, **kwargs ):
        """
        Return full url to portal
        """
        return self.host_url( self.portal_path( ename, evalue, **kwargs ) )

    def portal_path( self, ename=None, evalue=None, **kwargs ):
        """
        Return URL for the registered portal view, with extra name-value
        encoded in the url (for sku lookup, etc.) if provided.
        Defaults to the basic site urls for normal and extra, but
        portal url variations can be passed in kwargs.
        """
        if ename and evalue:
            portal = kwargs.pop( 'portal', 'portal_extra' )
            kwargs.update({ 'ename': ename, 'evalue': evalue })
        else:
            portal = kwargs.pop( 'portal', 'portal_view' )
        return reverse( portal, kwargs=kwargs )

    #-------------------------------------------------------------------

    def flag( self, flag, upstream=True ):
        """
        Check for flag setting in sandbox; by default return system flag
        setting if no sandbox flag is present.
        """
        flags = self.policy['flags']
        if flags and flag in flags:
            return flags[ flag ]
        if upstream:
            return sys_options.flags().get( flag, None )

    @property
    def email_staff( self ):
        return self._email_staff if self._email_staff else self.email_support
