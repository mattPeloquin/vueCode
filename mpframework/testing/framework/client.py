#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Customized test case clients
"""
from importlib import import_module
from django.conf import settings
from django.http import HttpRequest
from django.http import SimpleCookie
from django.contrib.auth import login as auth_login
from django.contrib.auth import authenticate
from django.test.client import Client
from django.test.client import ClientHandler

from mpframework.common.utils.user import session_cookie_name
from mpframework.common.utils.request import is_api_request
from mpframework.common.utils.request import get_referrer
from mpframework.common.logging.timing import mpTiming
from mpframework.common.logging.timing import mpTimingNone
from mpframework.user.mpuser.utils.login import logout_user


class mpClientHandler( ClientHandler ):
    """
    Support management of middleware request passed to views.
    The get_response call is hooked to grab a reference,
    which is then updated with test data. This allows the middleware
    processing to occur on the request, and makes test data
    available during context processing and rendering.
    """

    def __init__( self, *args, **kwargs ):
        super().__init__( *args, **kwargs )
        # Per-process holders for request and test data to inject
        self._stashed_request = None
        self._stashed_mptest = None

    def inject_mptest( self, mptest_data ):
        """
        HACK - call this before using the client handler to generate
        a response, to setup data that is added later to request.
        """
        self._stashed_mptest = mptest_data

    def get_response( self, request ):
        """
        Add injected data to the request.
        """
        request.mptest = self._stashed_mptest
        self._stashed_request = request
        response = super().get_response( request )
        return response

    def get_request( self ):
        return self._stashed_request


class mpClient( Client ):
    """
    For unit tests, add to the Django test client to support spoofing login for
    Sandboxes with unique sessions for each
    """

    def __init__( self, enforce_csrf_checks=False, **kwargs ):

        # Import engine here to avoid triggering DJ settings dependency
        self._engine = import_module( settings.SESSION_ENGINE )

        # Call GRANDPARENT init, so handler isn't created twice
        super( Client, self ).__init__( **kwargs )

        # From parent, exception management
        self.raise_request_exception = True
        self.exc_info = None
        self.extra = None

        # Replace Django test client handler with framework's
        self.handler = mpClientHandler( enforce_csrf_checks )

    def session( self ):
        """
        Override Django test request session mocking to use MPF cookie name
        """
        current_sandbox = getattr( self.handler, 'current_sandbox', None )
        if not current_sandbox:
            return

        cookie_name = session_cookie_name( current_sandbox )

        # Return existing session object if it is for current user
        cookie = self.cookies.get( cookie_name )
        if cookie:
            return self._engine.SessionStore( cookie.value )

        # Or create a new one
        session = self._engine.SessionStore()
        session.save()
        self.cookies[ cookie_name ] = session.session_key

        return session

    def login_sandbox( self, sandbox, user, password ):
        """
        Sets the Factory to appear as if it has successfully logged into a site.
        """
        self.handler.current_sandbox = sandbox

        user = authenticate( user=user, password=password )
        if not user or not user.is_active:
            return
        self.handler.current_user = user

        # Create mock request to store login details
        # and add user and sandbox to support login code that needs them
        request = self.mock_request( self.session() )
        request.uri = "LOGINTEST/{}".format( request.path )

        # Perform Django login on the user and set current sandbox
        auth_login( request, user )
        user.set_current_sandbox( sandbox )

        # Login cycles the session key, so save update to cookie
        # mocking and session store
        cookie_name = session_cookie_name( self.handler.current_sandbox )
        self.cookies[ cookie_name ] = request.session.session_key
        request.session.save()

        return user

    def logout( self ):
        """
        Override Django test logout, since the default logout will call authentication
        backend to get user to attach to dummy request, which doesn't work because
        MPF's backend expects to be called with a sandbox.
        Unlike the Django logout, MPF assumes the client has a valid
        session that was initialized for a particular sandbox.
        """
        if self.session():
            request = self.mock_request( self.session() )
            logout_user( request )

        self.cookies = SimpleCookie()

    def mock_request( self, session, sandbox=None, user=None, request=None ):
        """
        For testing without normal middleware processing (like login from
        non-view tests), make request object meets minimal MPF expectations.
        """
        request = request or HttpRequest()
        request.mptiming = mpTiming() if settings.DEBUG else mpTimingNone()

        request.session = session
        request.id = id( request )
        request.is_bad = False
        request.is_healthcheck = False
        request.is_lite = False
        request.is_api = is_api_request( request )
        request.referrer = get_referrer( request )

        user = user or getattr( self.handler, 'current_user', None )
        sandbox = sandbox or ( self.handler.current_sandbox if self.handler else None )

        request.sandbox = sandbox
        request.user = user
        request.skin = None
        request.mpinfo = {}
        request.mpstash = {}
        request.ip = '127.0.0.1'
        request.mpname = "p{}-{}-{}".format( sandbox._provider_id,
                    sandbox.subdomain, user )
        request.mpipname = "{}, {}".format( request.ip, request.mpname )

        return request
