#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Access checks implemented in middleware
"""
from django.conf import settings
from django.http import HttpResponseRedirect
from django.http import Http404
from django.urls import reverse

from mpframework.common import log
from mpframework.common.api import respond_api_expired
from mpframework.common.utils import request_is_authenticated
from mpframework.common.middleware import mpMiddlewareBase
from mpframework.common.cache.template import use_full_path_cache

from ..views.terms import accept_terms
from ..views.activate import not_verified


def view_response_for_request( request, view_fn, **kwargs ):
    """
    Call view with full path caching and return response as if it was the page for the URL
    Prevents the new response from being cached as the normal page
    """
    return view_fn( use_full_path_cache( request ), **kwargs )


class UserAccessMiddleware( mpMiddlewareBase ):
    """
    User access request validation

    To view non-public pages, user must be authenticated and meet other
    requirements such as initialization.
    Returning none allows the user request to move forward
    """
    _PUBLIC_URLS = [ '/{}'.format( url_prefix ) for
                url_prefix in settings.MP_URL_PATHS_PUBLIC ]
    _PORTAL_URL = '/{}'.format( settings.MP_URL_PORTAL )
    _NOHOST_URL = '/{}'.format( settings.MP_URL_NO_HOST )
    _NOHOST_URL_FT = '/{}'.format( settings.MP_URL_NO_HOST_FT )
    _login = reverse('login')

    def process_request( self, request ):
        """
        All HTTP requests to MPF and Django run through here.

        If user isn't authenticated and request requires login, go to login page.
        If user is marked as not active, they won't authenticate so login
        will show special lockout page.
        """
        if request.is_healthcheck or request.is_bad:
            return

        allow = False
        sandbox = request.sandbox
        user = request.user
        ipname = request.mpipname
        path = request.path
        uri = request.uri
        log.debug2("Checking request access: %s -> %s, %s", user, ipname, uri)

        # If there is a valid user object (from login or session) and they are
        # active and have access to sandbox, let them through
        if request_is_authenticated( request ):
            log.info4("Middleware allowing user: %s -> %s", ipname, uri)
            if user.is_active:
                if user.has_sandbox_access( sandbox ):
                    allow = True
                else:
                    log.warning("SUSPECT - user/sandbox invalid: %s", ipname)
            else:
                # FUTURE - provide a screen explaining user is locked out instead of 404
                log.info2("Deactivated user attempted access: %s", ipname)
                raise Http404

        # Allow various urls to carry on for later authentication
        elif self.middleware_allow( sandbox, path, uri, ipname ):
            allow = True

        if allow:
            # Let them through - access is validated later on views
            return

        # TEST HACK - handle local serving of visitor content
        if settings.MP_DEVWEB and path.startswith( settings.MP_URL_PROTECTED_XACCEL ):
            log.info("ALLOWING DEV VISITOR: %s -> %s", ipname, uri)
            return

        # If they get here, request is not allowed. Treat as a session
        # expiration, which will work for the most common case as
        # well as attack probing

        if request.is_api:
            log.info3("Middleware API deny: %s -> %s", ipname, uri)
            return respond_api_expired()

        if path == self._login:
            # Prevent looping if already redirected here
            log.info2("MIDDLEWARE RAISING 404 TO PREVENT LOOP: %s -> %s", ipname, uri)
            raise Http404

        log.info2("Visitor REJECT: %s -> %s %s", ipname, request.method, uri)
        return HttpResponseRedirect( self._login )

    @classmethod
    def middleware_allow( cls, sandbox, path, uri, ipname, msg='' ):
        """
        Returns true if url should not be blocked in this middleware
        """
        reason = None
        public = not sandbox.policy['private_portal']

        if public and path.count('/') == 1:
            reason = 'home'

        elif path.startswith( cls._NOHOST_URL ) or path.startswith( cls._NOHOST_URL_FT ):
            reason = 'no-host'

        elif public and path.startswith( cls._PORTAL_URL ):
            reason = 'portal'

        elif public and any( path.startswith( prefix ) for prefix in cls._PUBLIC_URLS ):
            reason = 'public'

        if reason:
            log.info3("Middleware allowing %s %s: %s -> %s", reason, msg, ipname, uri)
            return True

    def process_view( self, request, view_fn, view_args, view_kwargs ):
        """
        Make sure the user is in a valid state before allowing access to non-public content
        """
        if request.is_healthcheck or request.is_bad:
            return
        user = request.user
        sandbox = request.sandbox
        log.detail3("Middleware process_view: user(%s), path(%s)", user, request.uri)

        # Check email activation and terms
        if user and user.is_authenticated:

            # Skip if no need to check
            if user.is_ready( sandbox ):
                return

            # Skip any activation/term redirect in automated testing to make
            # setting up fixtures and view scenarios easier
            if settings.MP_TESTING:
                return

            # Skip pages that are validated later
            if self.middleware_allow( sandbox, request.path, request.uri,
                                      request.mpipname, 'view' ):
                return

            # Email activation
            # If user isn't verified, send to page where they can request new mail
            if not user.email_verified and request.sandbox.policy['verify_new_users']:
                log.info("Email not verified, redirecting view: %s -> %s", user, request.uri)
                return view_response_for_request( request, not_verified, **view_kwargs )

            # Make sure terms have been agreed to
            # Preserve any extra info in url to pass to portal
            if not user.terms_accepted:
                log.info("Terms not accepted, redirecting view: %s -> %s", user, request.uri)
                return view_response_for_request( request, accept_terms, **view_kwargs )
