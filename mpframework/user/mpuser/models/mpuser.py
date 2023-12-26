#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    MPF user model, which extends Django user
"""
from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.conf import settings

from mpframework.common import _
from mpframework.common import log
from mpframework.common import constants as mc
from mpframework.common.model import BaseModel
from mpframework.common.model import CachedModelMixin
from mpframework.common.model.fields import YamlField
from mpframework.common.model.fields import mpImageField
from mpframework.common.model.fields import mpDateTimeField
from mpframework.common.model.fields import TruncateCharField
from mpframework.common.cache import stash_method_rv
from mpframework.common.cache import invalidate_cache_group
from mpframework.common.compat import compat_static
from mpframework.common.delivery import use_compatibility
from mpframework.common.delivery import DELIVERY_MODES_ALL
from mpframework.common.utils import now
from mpframework.common.utils import join_urls
from mpframework.common.utils.file import unique_name
from mpframework.foundation.tenant.models.sandbox import Sandbox
from mpframework.foundation.tenant.models.provider import Provider

from .. import mpUserException
from ..cache import cache_group_user
from ..cache import cache_group_sandbox_user
from ..signals import mpuser_invalidate
from ..signals import mpuser_health_check
from .mpuser_manager import mpUserManager


class mpUser( CachedModelMixin, PermissionsMixin, BaseModel, AbstractBaseUser ):
    """
    Extends Django user with:

     - Multitenant user, staff, and security/access support
     - Connection point for other apps (Account, various extensions)
     - Proxy for external user support (OAuth, etc.)

    TBD - implement OAuth support
    TBD - move aspects of mpUser that optimize ties to other apps (au)
    """

    # The CURRENT email -- used for sandbox-unique username
    email = models.EmailField( db_index=True, max_length=mc.CHAR_LEN_UI_EMAIL )

    # Tell Django to work with the user-visible email as the username; note that
    # MPF overrides Django username behavior in most areas
    USERNAME_FIELD = 'email'

    """
    Sandbox and Provider

     - All mpUsers have a provider; many are also tied to 1 sandbox
     - Staff may be tied to one Provider's sandbox or all the sandboxes
     - Non-staff users are ALWAYS customers of ONE sandbox
     - Root staff can spoof sandbox and provider

    This supports the core end-customer case of separate logins and experiences
    for each sandbox, while support staff efficiency for both staff with
    multiple sandboxes and for root staff administration.

    The _provider and _sandbox DB fields are for persisting:

      'Normal users' -- tied to a single sandbox
      'Provider users' -- can log into any sandbox the provider owns

    'Provider user' is controlled by sandboxes_level; _sandbox should be null
    Provider id == MP_ROOT['PROVIDER_ID'] designates ROOT users

    'provider' and 'sandbox' properties manage current sandbox for 'Provider users'
    and ROOT spoofing. The DB values below capture the tenancy the user
    is tied to but should NOT be used for provider/sandbox state in user session.
    """
    _provider = models.ForeignKey( Provider, models.CASCADE,
                related_name='users', db_column='provider_id' )

    # NOTE - outside of admin, the _sandbox field is used primarily as an ID vs.
    # referenced directly as a Django model; see the sandbox property for details
    _sandbox = models.ForeignKey( Sandbox, models.SET_NULL,
                null=True, blank=True, related_name='users',
                verbose_name=_("Site"), db_column='sandbox_id' )

    """
    Staff access

    Django defines is_staff as basis for accessing admin site.
    MPF reworks and extends the notion of staff to content outside
    of the admin pages.

    is_staff is converted to a property based on staff_level (see below)

    Django's is_superuser flag is used to control access to setting
    staff levels and other staff-management functionality

    Staff level defines Level of staff features
    These adjust both visibility in UI and are used for backend verification.
    Options below can be set by superusers for their staff depending on teh
    provider privilege level.
    """
    STAFF_LEVELS = (
        ( None, _("No staff access") ),
        ( mc.STAFF_LEVEL_RO, _("Read-only") ),
        ( mc.STAFF_LEVEL_LOW, _("EasyVue") ),
        ( mc.STAFF_LEVEL_MED, _("BizVue") ),
        ( mc.STAFF_LEVEL_HIGH, _("SiteBuilder") ),
        ( mc.STAFF_LEVEL_ALL, _("SiteBuilder Pro") ),
        )
    ROOT_LEVELS = (
        ( mc.STAFF_LEVEL_ROOT, _("ROOT staff") ),
        ( mc.STAFF_LEVEL_ROOT_MENU, _("ROOT menus") ),
        ( mc.STAFF_LEVEL_ROOT_ALL, _("ROOT all") ),
        )
    _staff_level = models.IntegerField( choices=STAFF_LEVELS + ROOT_LEVELS,
                blank=True, null=True, db_column='staff_level'  )

    """
    'Provider users' and sandbox scope seen in the admin UI?

    Controls whether admin UI gives a flatlander view of the current sandbox
    vs. showing information for other sandboxes the provider owns.
    Staff users with privilege can configure this in the UI as with workflow,
    while in other cases it is set by provider to limit access
    """
    SANDBOXES_LEVEL = (
        ( 0, _("Only sees current site") ),
        ( 10, _("Sees all sites") ),
        )
    sandboxes_level = models.IntegerField( choices=SANDBOXES_LEVEL, default=0 )

    """
    UI Areas a staff user has access to
    Makes top-level staff menus visible for each area; may also
    adjust visibility of UI elements in other areas.
    Mostly used in the UI, not usually checked on backend!
    """
    staff_areas = models.CharField( max_length=8, blank=True )

    """
    Implement simple workflow that allows for working on unreleased items with
    promotion into production model. Although it is orthagonal from staff level,
    normally only staff have access to all the workflow states.
      - Production is seen by everyone (including visitors)
      - Beta is special; can be overridden in other areas such as account.
    """
    WFL_PROD = 0
    WFL_BETA = 1
    WFL_DEV = 2
    WORKFLOW_LEVEL = (
        ( WFL_PROD, _("Sees production") ),
        ( WFL_BETA, _("Sees beta") ),
        ( WFL_DEV, _("Sees development") ),
        )
    workflow_level = models.IntegerField( choices=WORKFLOW_LEVEL,
                default=WFL_PROD )

    # Add index to modified for use with timewin
    hist_modified = mpDateTimeField( db_index=True, default=now,
                verbose_name=_("Modified") )

    # Is user active? Used by Django as well as mpFramework, staff can set
    # to lock user out of system without affecting information
    is_active = models.BooleanField( default=True )

    # Flag that represents staff content related to owning a provider
    _is_owner = models.BooleanField( default=False, db_column='is_owner' )

    # Flag for providing two tier-access to portal content
    _extended_access = models.BooleanField( default=False )

    # Does the user see debug and platform UI that is in development?
    _has_test_access = models.BooleanField( default=False )

    # Is staff member currently set to user-view mode
    staff_user_view = models.BooleanField( default=False )

    # Override default sandbox delivery settings
    _delivery_mode = models.CharField( max_length=16, blank=True,
                choices=DELIVERY_MODES_ALL, db_column='delivery_mode' )

    #--------------------------------------------------------------------
    # Details on the user instance

    # Initialization/activation info
    init_terms = TruncateCharField( max_length=mc.CHAR_LEN_UI_LONG, blank=True )
    init_activation = TruncateCharField( max_length=mc.CHAR_LEN_UI_LONG, blank=True )
    email_verified = models.BooleanField( default=False )

    # User avatar image
    image = mpImageField( blank=True, null=True )

    # Key info on person, and keys controlled by staff, indexed for searching
    first_name = models.CharField( db_index=True, max_length=mc.CHAR_LEN_UI_DEFAULT )
    last_name = models.CharField( db_index=True, blank=True,
                max_length=mc.CHAR_LEN_UI_DEFAULT )
    organization = models.CharField( db_index=True, blank=True,
                max_length=mc.CHAR_LEN_UI_DEFAULT )
    title = models.CharField( db_index=True, blank=True,
                max_length=mc.CHAR_LEN_UI_DEFAULT )
    external_key = models.CharField( db_index=True, blank=True,
                max_length=mc.CHAR_LEN_UI_DEFAULT )
    external_group = models.CharField( db_index=True, blank=True,
                max_length=mc.CHAR_LEN_UI_DEFAULT )

    # Ancillary profile information
    comments = models.CharField( max_length=mc.CHAR_LEN_UI_BLURB, blank=True )
    external_tag = models.CharField( db_index=True, blank=True,
                max_length=mc.CHAR_LEN_UI_DEFAULT )
    external_tag2 = models.CharField( db_index=True, blank=True,
                max_length=mc.CHAR_LEN_UI_DEFAULT )
    external_tag3 = models.CharField( db_index=True, blank=True,
                max_length=mc.CHAR_LEN_UI_DEFAULT )

    # Per-user UI options/state, managed as JSON blob data by JS UI code
    email_changed = mpDateTimeField( null=True, blank=True )
    pwd_changed = mpDateTimeField( null=True, blank=True )

    # Configurable user options
    options = YamlField( null=True, blank=True )

    # Notes entered by staff; this is part of staff search
    notes = models.CharField( max_length=mc.CHAR_LEN_DB_SEARCH, blank=True )

    class Meta:
        verbose_name = _("User")

    objects = mpUserManager()

    """-------------------------------------------------------------------
        USER CACHING and STASHING

        User objects are created for every HTTP request and referenced
        heavily for access privileges, etc.
        Most users will have a 1:1 relationship with sandboxes, but users
        can be logged into multiple sandboxes, and the data cached on a
        per-sandbox basis is different.

        User manager's get_from_id caches just user data, tying users to
        request objects using the cache_group_user cache group.

        The user's default model cache_group is tied to sandbox user
        is currently logged into, so can invalidate data specific to
        the user and sandbox.

        Stashing is used extensively to capture values used multiple
        times within each request. This means much user state is frozen
        during a request response so won't reflect updates.
    """
    _clear_cache_names = ( 'session', )
    _clear_cache_field_names = ( '_sandbox', '_provider' )

    @property
    def cache_group( self ):
        return cache_group_sandbox_user( self )

    def invalidate( self ):
        super().invalidate()
        # Since default is sandbox user, also do just user dependencies
        invalidate_cache_group( cache_group_user( self.pk ) )
        mpuser_invalidate.send( sender=self.__class__, user=self )

    def _cache_extend( self ):
        """
        Support extensions adding/stashing info to user object before cache
        """
        pass

    #--------------------------------------------------------------------
    # MPF model support

    # For non-admin requests, user references cached sandbox and provider objects
    select_related = ()
    select_related_admin = select_related + ( '_provider', '_sandbox' )

    lookup_fields = ( 'id__iexact', 'email__icontains', 'first_name__icontains',
                'last_name__icontains' )

    @staticmethod
    def tenant_arg_filter( _model, sandbox, provider ):
        """
        Queryset tenant filter for users that includes provider staff that have
        access to all sandboxes under provider.
        """
        filter_args = ()
        filter_kwargs = {}
        if sandbox:
            filter_args = ( models.Q( _sandbox = sandbox ) |
                            models.Q( _sandbox__isnull = True ) ,)
            provider = sandbox.provider
        if provider:
            filter_kwargs['_provider'] = provider
        return filter_args, filter_kwargs

    def __init__( self, *args, **kwargs ):
        super().__init__( *args, **kwargs )

        # Manage current session sandbox apart from stored sandbox in DB
        # This is primarily to support users than can access more than
        # one sandbox, but also avoids DB hits by using cached sandbox object
        self._current_sandbox = None

    def __str__( self ):
        if self.dev_mode:
            return "{}({}s{})".format( self.email, self.pk, self._sandbox_id )
        return self.email

    def clone( self, **kwargs ):
        raise mpUserException("mpUsers should never be cloned: %s" % self)

    def _log_instance( self, message ):
        log.debug_on() and log.detail("{} mpUser: {}-{} ({})".format( message,
                                                        self.email, self.pk, id(self)))
    @stash_method_rv
    def public_storage_name( self, name ):
        """
        Unique filename for user uploads
        """
        rv = '{}-{}-{}_{}'.format( self.provider.resource_path, self.sandbox.resource_path,
                    self.email, unique_name( name ) )
        log.debug("User public_storage_name %s: %s -> %s", self, name, rv)
        return rv

    @property
    def public_storage_path( self ):
        """
        All users share a system-wide users folder
        """
        return self.provider.policy.get( 'storage.users', '_users' )

    @property
    @stash_method_rv
    def media_url( self ):
        """
        Provide full URL to public resource/upload folder
        """
        return compat_static( join_urls( settings.MEDIA_URL, self.public_storage_path ),
                              self.use_compat_urls )
    @property
    def dict( self ):
        # Note tracking should be select_related to user object for efficiency
        return {
            'id': self.pk,
            'email': self.email,
            'first': self.first_name,
            'last': self.last_name,
            'name': self._name,
            'org': self.organization,
            'tag1': self.external_tag,
            'tag2': self.external_tag2,
            'tag3': self.external_tag3,
            }

    """---------------------------------------------------------------
        Tenancy-related staff/root access

        Tenancy and permutations of staff access to both root and
        provider areas are managed via these methods.
        All users have a provider. If they have a sandbox, they are
        tied to that sandbox.
        When user objects are instantiated, they are assigned a
        current sandbox based on request or other context; obviously
        that sandbox must match tenancy rules.
    """

    @property
    def sandbox( self ):
        """
        Current request/session sandbox
        Normally this will be set before use by user backend, but handle cases
        where user is instantiated without a sandbox.
        """
        if not self._current_sandbox:

            if self._sandbox_id:
                # Set lazily for non-request cases with normal users
                # Get Sandbox through caching vs. just assigning to avoid DB hit
                self._current_sandbox = Sandbox.objects.get_sandbox_from_id(
                            self._sandbox_id, self._provider_id )
            else:
                log.info("User sandbox outside request, setting to first: %s", self)
                # HACK - set to first sandbox for provider if provider user
                # Only staff should have access to multiple sandboxes
                self._current_sandbox = self._provider.my_sandboxes.all()[0]

            log.debug("Set user sandbox during get: %s", self)

        return self._current_sandbox

    def set_current_sandbox( self, sandbox ):
        """
        Set the sandbox as the user's current, throw exception if
        tennancy is violated.
        """
        assert sandbox or settings.MP_TESTING

        if not self.has_sandbox_access( sandbox ):
            raise mpUserException("SUSPECT - SANDBOX OUTSIDE TENANCY:"
                        " %s, %s" % (self, sandbox))

        self._current_sandbox = sandbox

        # Make sure permissions are updated if needed
        self.set_max_level()

    @property
    def provider( self ):
        """
        Current session provider
        Supports root spoofing logins by simulating provider of the current sandbox
        for the root -- for non-root users, current provider should always
        be the one stored in the DB.
        """
        if self.is_root:
            rv = self.sandbox.provider
        else:
            rv = self._provider
        return rv

    @property
    def is_root( self ):
        """
        Does this user have privileges to log into any provider's sandbox?
        This is separate from staff and root staff privleges.
        """
        return self._provider_id == settings.MP_ROOT['PROVIDER_ID']

    @property
    @stash_method_rv
    def is_root_staff( self ):
        """
        Is this a root-staff user? This check is separate from the current
        root access level of a root user, which can change if they are spoofing.
        """
        return bool( self.is_root and self.is_active and self._staff_level and
                     self._staff_level >= mc.STAFF_LEVEL_ROOT )

    @property
    def logged_into_root( self ):
        """
        Return true if this is root user in root console
        """
        logged_into_root = bool( self.sandbox and self.sandbox.is_root )
        if logged_into_root and not self.access_root:
            raise mpUserException("SUSPECT ATTACK - ROOT attempted access:"
                    " %s" % self)
        return logged_into_root

    def logged_into_root_request( self, request ):
        """
        Adds additional checks based on a request
        """
        if self.logged_into_root:
            if request.sandbox != self.sandbox:
                raise mpUserException("SUSPECT ATTACK - ROOT sandboxes:"
                        " %s -> %s" % (self, request.sandbox))
            return True

    @stash_method_rv
    def is_ready( self, sandbox=None ):
        """
        Is the user in good standing; this assumes that the activated and
        terms fields have been filled.
        If provided or available, also checks for optional sandbox rules.
        """
        rv = bool( self.is_active and self.activated and self.terms_accepted )
        sandbox = sandbox or self.sandbox
        if sandbox:
            verified = ( not sandbox.policy['verify_new_users'] or
                    self.email_verified )
            rv = rv and verified
        return rv

    @property
    @stash_method_rv
    def is_staff( self ):
        """
        Override Django property based on staff levels
        Don't allow setting programmatically
        """
        return bool( self.is_active and self.staff_level > mc.STAFF_LEVEL_NONE )
    @is_staff.setter
    def is_staff( self, value ):
        log.error("Attempt to set mpUser is_staff: %s", self)

    @property
    def is_owner( self ):
        """
        Does this user have provider owner/staff privileges
        """
        return bool( self.is_staff and (self._is_owner or self.is_root_staff) )

    @property
    def sees_sandboxes( self ):
        """
        Determines whether the staff UI shows items from all of a provider's sandboxes
        """
        return self.sandboxes_level > 0 and not self.provider.isolate_sandboxes

    def has_sandbox_access( self, sandbox ):
        """
        Does this user have access to sandbox?
        Does not care if the user is authenticated against the sandbox
        """
        if self.is_root:
            return True
        elif self.sees_sandboxes:
            return sandbox._provider_id == self.provider.pk
        else:
            return sandbox.pk == self._sandbox_id

    @property
    def has_test_access( self ):
        if self.is_root_staff:
            return True
        # HACK - make testing menus always available to E2E testing
        if settings.MP_TESTING_E2E or self.sandbox.policy['test_site']:
            return True
        return self._has_test_access

    @property
    def extended_access( self ):
        if self.is_root_staff:
            return True
        return self._extended_access

    @property
    @stash_method_rv
    def staff_level( self ):
        """
        The effective staff access level.
        Normal staff only have the level set in the database.
        Root staff can spoof the staff level for a session by having this return the
        maximum staff level for the current sandbox.
        """
        return self._staff_level or 0

    """---------------------------------------------------------------
        Helpers for staff features/areas permissions
    """
    @property
    def workflow_beta( self ):
        return 'B' in self.workflow_filters
    @property
    def workflow_dev( self ):
        return self.workflow_level > self.WFL_BETA

    @property
    def access_root( self ):
        return bool( self.is_root_staff and self.staff_level >= mc.STAFF_LEVEL_ROOT )
    @property
    def access_root_menu( self ):
        return self.logged_into_root or self.staff_level >= mc.STAFF_LEVEL_ROOT_MENU
    @property
    def access_root_all( self ):
        return self.is_root_staff and self.staff_level >= mc.STAFF_LEVEL_ROOT_ALL
    @property
    def access_staff( self ):
        return self.is_staff
    @property
    def access_staff_view( self ):
        # Is user staff AND not disabled for staff user spoofing
        return self.access_staff and not self.staff_user_view
    @property
    def access_ro(self):
        # LIMIT privilege check, so returns true for bad cases as a fail-safe
        return not self.access_staff or self.staff_level <= mc.STAFF_LEVEL_RO
    def _access( self, level ):
        return self.access_staff and self.staff_level >= level
    @property
    def access_low( self ):
        return self._access( mc.STAFF_LEVEL_LOW )
    @property
    def access_med( self ):
        return self._access( mc.STAFF_LEVEL_MED )
    @property
    def access_high( self ):
        return self._access( mc.STAFF_LEVEL_HIGH )
    @property
    def access_all( self ):
        return self._access( mc.STAFF_LEVEL_ALL )

    def _area_access( self, area ):
        return self.access_staff_view and bool(
                    not self.staff_areas or ( area.lower() in self.staff_areas.lower() ))
    @property
    def sees_user( self ):
        return self._area_access('U')
    @property
    def sees_content( self ):
        return self._area_access('C')
    @property
    def sees_licensing( self ):
        return self._area_access('L')
    @property
    def sees_group( self ):
        return self._area_access('G') and self.access_high
    @property
    def sees_sandbox( self ):
        return self._area_access('S') and self.access_high

    def set_max_level( self, max_level=None, save=False ):
        """
        Adjust user's level to match the given maximum level, or sandbox default
        Always take away privilege if staff level is higher, but support
        move level up for account owners for onboarding experimentation
        and upgrade/downgrade semantics for provider accounts.
        """
        max_level = max_level or (
                self.sandbox.policy['staff_level_max'] or self.staff_level )
        if max_level >= mc.STAFF_LEVEL_ROOT:
            log.info3("Skipping set_max_level root privilege: %s", self)

        # Adjust the staff level to new ceiling
        dirty = False
        if not self.is_root_staff and (
                ( self.staff_level > max_level ) or
                ( self.is_owner and self.staff_level < max_level ) ):
            log.info2("STAFF LEVEL %s -> %s by %s", self.staff_level, max_level, self)
            self._staff_level = max_level
            dirty = True

        dirty and save and self.save()

    #--------------------------------------------------------------------
    # Naming methods including Django methods

    def get_username( self ):
        return self.username

    def get_full_name( self ):
        return self.name

    def get_short_name( self ):
        return self.first_name if self.first_name else self.email

    @property
    def username( self ):
        """
        Provide some abstraction for username, for future flexibility and readability
        """
        return self.email

    @property
    def name( self ):
        """
        Provide a UI name for the user, based on the information they
        have entered
        """
        if self.last_name and self.first_name:
            return self._name
        else:
            return self.email

    @property
    def _name( self ):
        return "{} {}".format( self.first_name, self.last_name )

    @property
    def log_name( self ):
        return "s{} {}".format( self.sandbox.pk, self.email )

    @property
    def workflow_name( self ):
        return self._WORKFLOW_NAME.get( self.workflow_level )
    _WORKFLOW_NAME = {
        WFL_PROD: 'prod',
        WFL_BETA: 'beta',
        WFL_DEV: 'dev',
        }

    @property
    def workflow_filters( self ):
        """
        What content workflow states can this user see?
        By default can see what is in production and what is
        "production retired" (accessed in the past but retired now)
        """
        rv = ['P']
        if self.is_ready():
            rv.append('Q')
            if self.workflow_level >= self.WFL_BETA:
                rv.append('B')
            if self.workflow_dev:
                rv.append('D')
        return rv

    #--------------------------------------------------------------------

    def delivery_mode( self, default=None ):
        """
        Handles any overrides of the sandbox default delivery mode
        """
        if self._delivery_mode:
            return self._delivery_mode
        return default if default else self.sandbox.delivery_mode

    @property
    @stash_method_rv
    def compatibility_on( self ):
        return use_compatibility( self.delivery_mode() )

    @property
    @stash_method_rv
    def use_compat_urls( self ):
        if self.options['use_compat_urls']:
            return True
        return self.sandbox.options['use_compat_urls']

    @property
    def activated( self ):
        return bool( self.init_activation )

    @property
    def terms_accepted( self ):
        return bool( self.init_terms )

    @property
    def image_url( self ):
        return self.image.url if self.image else ''

    def update_username( self, new_email ):
        """
        Update username and related email fields to use new email
        Full username different for provider-wide vs. sandbox-wide user, and
        that the sandbox will be loaded from DB for this operation
        """
        self.notes += "User changed email: {} -> {}".format( self.email, new_email )
        self.email = new_email
        self.email_changed = now()
        self.save()

    def health_check( self, sandbox=None, create_info=None, dirty=False ):
        """
        Regularly ensure that user data makes sense; this is used both for initialization
        and to handle deltas and self healing corrupt data.
        """
        if sandbox:
            # Tenancy sanity checks
            if not self.is_root:
                if sandbox._provider_id != self._provider_id:
                    raise mpUserException("SUSPECT - Attempt login outside provider:"
                                " %s -> %s" % (self, sandbox))
                if self._sandbox_id and self._sandbox_id != sandbox.id:
                    raise mpUserException("SUSPECT - Attempt login wrong sandbox:"
                                " %s -> %s" % (self, sandbox))

            # Set current sandbox (doesn't affect DB)
            self.set_current_sandbox( sandbox )

        if self.sees_sandboxes and self._sandbox_id:
            log.warning("HEAL USER - Sees sandboxes with sandbox set: %s", self)
            self._sandbox_id = None
            dirty = True

        if not self.activated:

            # If email is marked as verified, but user isn't active, assume
            # an admin override of a botched email verification
            if self.email_verified:
                log.debug("Activating user based on email verification being true: %s", self)
                self.init_activation = "EMAIL ACTIVATED: {} - {}".format( self.email, now() )
                dirty = True

            # If user is a provider without sandbox, or sandbox doesn't care about
            # activation, set as activated
            if not self._sandbox or not self._sandbox.policy['verify_new_users']:
                log.debug("Activating user, since out of whack with sandbox: %s", self)
                self.init_activation = "SITE ACTIVATED: {} - {}".format( self.email, now() )
                dirty = True

        # Let apps external to user model know they should check health
        mpuser_health_check.send( sender=self.__class__, user=self, create_info=create_info )

        if dirty:
            self.save()
