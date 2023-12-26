#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    REPLACE Django SessionMiddleware for MPF tenancy, security,
    and feature support.
"""
import time
from importlib import import_module
from django.conf import settings
from django.utils.http import http_date
from django.contrib.sessions.backends.base import UpdateError

from mpframework.common import log
from mpframework.common import sys_options
from mpframework.common.utils.user import session_cookie_name
from mpframework.common.middleware import mpMiddlewareBase


_engine = import_module( settings.SESSION_ENGINE )


class mpSessionMiddleware( mpMiddlewareBase ):
    """
    Manage session cookies
    MPF uses session cookies for all visitors. The cached session
    info is used for authentication, tracking, and preventing
    session abuse.
    """

    def process_request( self, request ):
        """
        Override Django request.session, with session based on sandbox
        """
        request.session = None
        if request.is_lite or request.is_bad:
            return

        # Try to get session from cookie (normal logged in case),
        # then see if it has been passed as a query string, which is done
        # to cross domains (for sandboxes redirected to https main site)
        cookie_name = session_cookie_name( request.sandbox )
        session_key = request.COOKIES.get( cookie_name )
        if not session_key:
            session_key = request.GET.get( cookie_name )

        # Get session object and attach to request
        if session_key:
            request.session = _engine.SessionStore( session_key )

            # If session was marked as new, note that it has been setup
            if request.session.get('visitor_session'):
                request.session['visitor_session'] = False

            # Some security audits want csrf preserved with session
            csrf = request.META.get( settings.CSRF_HEADER_NAME )
            if csrf:
                request.session['csrf'] = csrf

            # FUTURE SECURE - store device info in session, prevent session
            # from being used across devices to prevent one user account
            # login/session cookie from being used across multiple

        # Otherwise, this is new request without a session, mark it
        # to force creation for both soon-to-be authenticated users and
        # anonymous visitor tracking
        elif not request.is_api:
            request.session = _engine.SessionStore()
            request.session.set_expiry( settings.MP_USER_SESSION_AGE_SHORT )
            if sys_options.disable_non_critical():
                return
            if request.sandbox.flag('TRACKING_visitors'):
                request.session['visitor_session'] = True

        log.info3("Session %s, %s: %s -> %s", cookie_name, request.mpipname,
                    request.uri, request.session and request.session._session)

    def process_response( self, request, response ):
        """
        Set user session cookie based on sandbox.
        If request.session was modified and the user is valid, save changes
        and set session cookie.
        NOTE - nginx will not cache any response with Set-Cookie
        """
        if request.is_lite or request.is_bad or not request.session:
            return response

        user = request.user
        session = request.session
        cookie_name = session_cookie_name( request.sandbox )

        # Cookie should be deleted if the session is not being used
        if cookie_name in request.COOKIES and session.is_empty():
            log.info2("Deleting session cookie: %s", request.mpipname )
            response.delete_cookie( cookie_name )
            return response

        try:
            if not session.modified:
                # If session key passed in url, or popup close request,
                # mark as modifed to force setting cookie
                if request.GET.get( cookie_name ) or request.is_popup_close:
                    session.modified = True

            # Save session and write the cookie if needed
            if( session.modified and not session.is_empty() and

                    # Don't save cookie/session for ajax requests; seen this
                    # reset cookie and ajax requests don't establish session
                    # FUTURE - will need to redo with ajax login
                    not request.is_api and

                    # Don't send cookies if major problem as per Django #3881
                    response.status_code != 500
                    ):
                try:
                    # Saving a session with content and no key generates new key
                    session.save()
                except UpdateError:
                    log.info("SUSPECT - Session cookie gone before request done: %s",
                                request.mpipname )
                else:
                    # Manage the session persistence (via cookie lifetime)
                    # based on remember me options
                    if session.get_expire_at_browser_close():
                        max_age = None
                        expires = None
                    else:
                        max_age = session.get_expiry_age()
                        expires = http_date( time.time() + max_age )

                    response.set_cookie(
                            cookie_name,
                            session.session_key,
                            max_age=max_age, expires=expires,
                            # Support non-https portals, but mirror request to
                            # ensure staff cookies aren't compromised
                            secure=request.is_secure(),
                            # Restrict cookie to only the host for this request
                            domain=None,
                            # Don't restrict cookie to any particular path
                            path='/',
                            # Don't allow cookie to be accessed by JS
                            httponly=True,
                            )
                    log.info3("Setting session cookie: %s, %s -> %s, %s",
                                user, request.uri, cookie_name, session.session_key)

        except AttributeError as e:
            log.warning("mpSessionMiddleware response error: %s, %s -> %s",
                        request.mpipname, request.uri, e)

        return response
