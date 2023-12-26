#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Override Django AnonymousUser to support MPF methods necessary
    for optional visitor access to portal.
"""
from django.conf import settings
from django.contrib import auth

from mpframework.common.cache import stash_method_rv
from mpframework.common.model import CachedModelMixin
from mpframework.common.utils import SafeNestedDict
from mpframework.common.delivery import use_compatibility


class Visitor( CachedModelMixin, auth.models.AnonymousUser ):
    """
    Used when user is not authenticated (visitor in MPF terminology).

    Provides a subset of necessary mpUser attributes and state.
    Visitors are attached to Django sessions and use the session for storing
    a subset of the mpUser data.

    For all requests, after mpAuthenticateMiddleware is called, the user object
    is a Visitor or mpUser -- there's no morphing between them.

    Dynamic properties are set in constructor.
    HACK - Items set as class members MUST NEVER BE MODIFIED - when there
    is risk from a coding error, use properties instead.
    """
    _password = False

    name = ""
    first_name = "Visitor"
    last_name = ""
    organization = ""
    title = ""
    external_key = ""
    external_group = ""

    workflow_dev = False
    workflow_beta = False
    email_verified = False
    terms_accepted = False
    activated = False
    last_login = None

    staff_areas = ''
    logged_into_root = False
    sees_sandboxes = False
    sandboxes_level = 0
    staff_user_view = False
    has_test_access = False
    access_root = False
    access_staff = False
    access_staff_view = False
    access_low = False
    access_med = False
    access_high = False
    access_all = False

    account_user = None
    au = None

    def __init__( self, request ):
        """
        Store any information necessary across user requests in the
        request session object (which will normally exist).
        """
        sandbox = request.sandbox
        assert sandbox
        super().__init__()
        self._session = request.session or {}
        self.sandbox = sandbox
        self._sandbox_id = sandbox.pk
        self.provider = sandbox.provider
        self._provider_id = sandbox._provider_id
        self.current_ip = request.ip
        self.options = SafeNestedDict( self._session.get( 'visitor_options', {} ) )

    def save( self ):
        self._session['visitor_options'] = self.options

    def __str__( self ):
        if settings.DEBUG:
            return "Visitor(s:{},p:{}->{})".format( self._sandbox_id,
                        self._provider_id, self.current_ip )
        else:
            return "Visitor({})".format( self.current_ip )

    def is_ready( self, sandbox=None ):
        return False

    @property
    def email( self ):
        return "visitor@{}".format( self.current_ip )

    @property
    def log_name( self ):
        return 's{} {}'.format( self._sandbox_id, self.email )

    @property
    def unique_key( self ):
        return 'Visitor{}'.format( self._session.session_key )

    @property
    def is_root( self ):
        return False

    @property
    def is_owner( self ):
        return False

    @property
    def staff_level( self ):
        return

    @property
    def workflow_level( self ):
        return 0

    @property
    def workflow_filters( self ):
        return ['P']

    @property
    @stash_method_rv
    def compatibility_on( self ):
        return use_compatibility( self.sandbox.delivery_mode )

    @property
    @stash_method_rv
    def use_compat_urls( self ):
        return self.sandbox.options['use_compat_urls']

    def delivery_mode( self, default=None ):
        return default if default else self.sandbox.delivery_mode

    def has_sandbox_access( self, sandbox ):
        return sandbox.pk == self._sandbox_id
