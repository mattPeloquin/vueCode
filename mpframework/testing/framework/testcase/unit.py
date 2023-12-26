#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared model/view unit test case code

    HACK - SOME HARDCODING RELATED TO TEST FIXTURES IN THIS MODULE
"""
from django.conf import settings
from django.db.models import Q
from django.test import TransactionTestCase
from django.test.utils import override_settings

from mpframework.foundation.tenant.models.sandbox import Sandbox
from mpframework.user.mpuser.models import mpUser
from mpframework.user.mpuser.models.visitor import Visitor

from ..client import mpClient
from .mixin import mpTestCaseMixin


@override_settings(
        EMAIL_BACKEND='mpframework.testing.framework.testcase.mixin.TestEmailBackend' )
@override_settings( DEBUG=settings.DEBUG )
class UnitTestCase( mpTestCaseMixin, TransactionTestCase ):
    """
    Base test case for Django model and view tests

    UnitTestCase instances can be used to test particular users against a
    particular sandbox; these must be initialized before use
    """
    client_class = mpClient

    def setUp( self ):
        super().setUp()

        # These are used by test infrastructure to manage state and reporting
        self.current_sandbox = None
        self.current_user = None

    """-------------------------------------------------------------------
        Tenant state management

        Users and what they can see are tied to specific sandboxes, so
        many tests in the system need to be carried out with
        different user/sandbox login combinations

        This adds to the login functionality of the Django test client (self.client)

        NOTE the assumption is that for each test case, the sandbox set
        in the test case will reflect the last time login() was called,
        UNLESS the sandbox was setup at the start of the test case.
    """

    def sandbox_init( self, sandbox_id=None, host_url=None, reset=False ):
        """
        Sets up enough state to fake sandbox url

        If sandbox state is already set, do not override unless reset forced
        to allow setting up sandbox options at start of test case
        For login cases, this is part of the login process.

        Tests that don't require login but do require sandbox
        (like non-login views) call this directly.
        """
        self.logout()
        if sandbox_id or not self.current_sandbox or reset:
            if sandbox_id:
                sandbox = Sandbox.objects.get( id=sandbox_id )
            else:
                # Root is always first sandbox, so take NEXT one as default
                # since root url has special checks on it
                sandbox = Sandbox.objects.filter()[1]
            self.ld("Sandbox initialized: %s", sandbox)
            self.current_sandbox = sandbox

            # Setup default visitor login by creating session and mock request
            self.client.handler.current_sandbox = sandbox
            session = self.client.session()
            mock_request = type( '', (), {} )()
            mock_request.sandbox = sandbox
            mock_request.session = session
            mock_request.ip = '127.0.0.1'
            self.current_user = Visitor( mock_request )

        # Need host_url to manufacture mocked requests
        self.host_url = ( host_url if host_url else
                self.current_sandbox.hosts.filter( main=True ).first().host_name )

        self.ld("Setup test sandbox: %s - %s", self.current_sandbox, self.host_url)

    def login( self, user_id, sandbox_id=None, host_url=None, reset=False ):
        """
        Login the given user id and setup sandbox
        Sets user in test case and returns

        Tries to reset as little as possible to optimize test speed.
        If sandbox and host_url are not specified, defaults
        are pulled from data relationship to user.
        """
        reset_user = not self.current_user or self.current_user.pk != user_id
        if reset or reset_user:
            # Get new user via MPF backend, which (includes
            # caching, extra select_related fields, etc.)
            user = self.get_user( user_id, sandbox_id )
            assert user, "TEST - No user with id: %s" % user_id
        else:
            user = self.current_user

        # If no sandbox provided, figure out from user, or get first one from provider
        if not sandbox_id and user.is_root:
            sandbox_id = 20
        if not sandbox_id:
            sandbox_id = user._sandbox_id
        if not sandbox_id:
            sandbox_id = user._provider.my_sandboxes.all()[0].pk

        # Reset the client state
        if reset:
            self.client = self.client_class()

        reset_sandbox = not self.current_sandbox or self.current_sandbox.pk != sandbox_id

        if reset or reset_sandbox:

            # Set the sandbox this login will be used with
            self.sandbox_init( sandbox_id, host_url=host_url, reset=True )

        # Reset user
        if reset or reset_user or reset_sandbox:

            # Make sure any existing user is logged out to mock
            # real-world Django session management
            if self.current_user:
                self.logout()

            # Fake login the user to create dummy session; note this creates
            # another full mpUser object which is just thrown away
            user = self.client.login_sandbox( self.current_sandbox, user, self.TEST_PWD )

            # Simulate ensuring user health, which occurs on regular login
            if user:
                user.health_check( self.current_sandbox, dirty=True )

            self.l("LOGIN %s -> %s", user, self.current_sandbox )
            self.current_user = user

        return self.current_user

    def get_user( self, userid=20, sandbox_id=None ):
        """
        Get user record without logging in
        Option to set sandbox to one owned by provider, or fist one by default
        """
        user = mpUser.objects.get_from_id( None, userid )
        if not sandbox_id:
            sandbox_id = user._sandbox_id
        self.sandbox_init( sandbox_id )
        user.set_current_sandbox( self.current_sandbox )
        return user

    def logout( self ):
        """
        Make sure any changes to user are saved, while also invalidating
        """
        self.ls("LOGOUT %s -> %s", self.current_sandbox, self.current_user )
        if self.current_user:
            self.current_user.save()
            self.current_user = None
            self.client.logout()

    def _get_first_valid_row( self, model ):
        """
        Returns a valid pk for the model that can be tested based on current sandbox

        This makes test fixture data less brittle, by allowing for
        testing different sandbox/user combinations while only needing to
        make sure the data exists in the fixture, not keep track of ids
        for which items are assigned to which provider and sandbox
        """

        # HACK - filters test data based on the sandbox being used, with code
        # similar to logic from common.admin.tenant to follow known
        # links back to the sandbox relationship
        from mpframework.common.model.utils import field_names
        fields = field_names( model )
        try:
            # Get first item that matches sandbox
            if 'sandbox' in fields:
                return model.objects.filter( sandbox_id=self.current_sandbox.pk ).first().pk
            if '_sandbox' in fields:
                return model.objects.filter( _sandbox_id=self.current_sandbox.pk ).first().pk

            # Get first item that matches provider owning current sandbox
            if '_provider' in fields:
                return model.objects.filter( _provider__my_sandboxes__id=self.current_sandbox.pk ).first().pk

            # Get first provider optional attached to provider or first system
            if 'provider_optional' in fields:
                return model.objects.filter( Q( provider_optional=self.current_sandbox.provider ) |
                                             Q( provider_optional__isnull=True ) ).first().pk

        except Exception as e:
            self.l("Exception _get_first_valid_row: %s -> %s", model, e)
            raise

        # If model doesn't have sandbox/provider fields, or a relationship
        # doesn't exist, just try the first row
        return model.objects.first().pk


    """--------------------------------------------------------------------
        Test user/sandbox support

        HACK -- These methods have defaults and other connections that
        are hard-coded to test fixture data - maybe make a mixin
    """

    def login_user( self, id=20, **kwargs ):
        return self.login( id, **kwargs )

    def login_root( self, sandbox_id=None, **kwargs ):
        # Root users can login in different sandboxes
        return self.login( 1, sandbox_id, **kwargs )

    def login_owner( self, id=12, sandbox_id=None, **kwargs ):
        return self.login( id, sandbox_id, **kwargs )

    def login_groupadmin( self, **kwargs ):
        return self.login( 21, **kwargs )
    def login_nogroup( self, **kwargs ):
        return self.login( 22, **kwargs )
    def login_notready( self, **kwargs ):
        return self.login( 23, **kwargs )

    # High and low-privilege single-sandbox staff accounts
    def login_staff( self, **kwargs ):
        return self.login( 103, **kwargs )
    def login_staff_high( self, **kwargs ):
        return self.login( 107, **kwargs )
    def login_staff_low( self, **kwargs ):
        return self.login( 101, **kwargs )

    def get_root_user( self, sandbox_id=None, id=1 ):
        return self.get_user( id, sandbox_id )
