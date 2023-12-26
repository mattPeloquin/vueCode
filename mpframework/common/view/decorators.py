#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    View decorators related to user access
"""
from functools import wraps
from django.conf import settings
from django.http import HttpRequest
from django.http import HttpResponseRedirect
from django.http import Http404

from .. import log
from ..utils import request_is_authenticated
from ..utils.login import authenticate_error_response


"""-------------------------------------------------------------------
    SSL view required

    To support easy CNAME redirection of sites, providers have the option
    to accept the risk of MitM user session hijacking by allowing HTTP.
    However, MPF does not allow login, staff screen, or other
    sensitive screens to be accessed over non HTTPS requests.
"""

def ssl_required( view_fn ):

    @wraps( view_fn )
    def wrapper( *args, **kwargs ):
        return _ssl_required( _get_request(*args), view_fn, *args, **kwargs )

    return wrapper

def _ssl_required( request, view_fn, *args, **kwargs ):

    if not request.is_secure() and settings.MP_CLOUD:
        return HttpResponseRedirect( '{}{}'.format( request.sandbox.main_host_ssl,
                                                    request.path ) )

    return view_fn( *args, **kwargs )


"""-------------------------------------------------------------------
    Admin View Access Validators

    There are multiple levels of view validation for screens/APIs:

      - Only seen by root staff
      - Only used by provider's staff (based on permissions)
      - Require user login (with checks for protected content)
      - Optionally (by sandbox or content) allow visitors
      - Are always public

    IT IS UP TO EACH VIEW and API RESPONSE to ensure that it does not show
    or otherwise allow access that violates provider/sandbox scope.

    Front-line filtering for login occurs in UserAccessMiddleware.process_request,
    which allows the following default behavior (no access decorator) for views:

        - Always public
        - Accessible to public unless private_portal is True

    The Django login_required decorator is replaced here for use with requests that:

        - Require login even if private_portal is False

    Filtering for ADMIN staff screens occurs in StaffAdminSite and RootAdminSite,
    so root_only and staff_required:

        - Are not used/needed for staff admin screens
        - Are used for staff screens/api outside the admin

    For admin screens they provide defense in depth against programming errors and edge
    cases where assumptions about path access, etc. break down.
    They also provide code documentation.

    Attempts to access a view the user does not have rights to will redirect to sandbox
    login screen for the sandbox while api views will return expired=true
"""

def login_required( view_fn ):
    """
    Only users who are logged in can access this API or screen
    """
    @wraps( view_fn )
    def wrapper( *args, **kwargs ):
        request = _get_request( *args )

        if request_is_authenticated( request ):
            return view_fn( *args, **kwargs )

        return authenticate_error_response( request )
    return wrapper

def staff_required( fn=None, **options ):
    """
    Only users marked as staff and valid for the sandbox can use this url,
    and they must do it over SSL
    """
    owner = options.get( 'owner', False )

    def decorator( view_fn ):
        @wraps( view_fn )
        def wrapper( *args, **kwargs ):
            request = _get_request( *args )
            if request_is_authenticated( request ):
                user = request.user
                if user.access_staff:
                    if not owner or user.is_owner:

                        if not request.sandbox.options['staff.unsecure']:
                            return _ssl_required( request, view_fn, *args, **kwargs )
                        else:
                            return view_fn( *args, **kwargs )

                log.info2("STAFF VIOLATION: %s", request.mpipname)

            return authenticate_error_response( request )

        return wrapper

    # Call outer on first pass if there are options, otherwise return it
    return decorator( fn ) if callable( fn ) else decorator

def root_only( view_fn ):

    @wraps( view_fn )
    def wrapper( *args, **kwargs ):
        request = _get_request( *args )

        if request_is_authenticated( request ):

            if getattr( request.user, 'is_root', False ):
                return _ssl_required( request, view_fn, *args, **kwargs )

            log.warning("ROOT VIOLATION: %s -> %s", request.mpipname, request.uri)

            # Raise 404 so these cases don't look any different than a random URL
            raise Http404

        return authenticate_error_response( request )
    return wrapper

def _get_request( *args ):
    """
    Support view decorators on module or class views by determining
    what type a wrapped view function is based request in first or second arg
    """
    for i in range( 2 ):
        if isinstance( args[i], HttpRequest ):
            return args[i]

    raise Exception("_get_request used on non-view function")
