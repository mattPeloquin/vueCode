#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Django Admin specializations for staff UI
"""
from django.conf import settings

from .. import log
from ..utils import request_is_authenticated
from ..utils.login import redirect_login
from .base import BaseAdminSite


# HACK - keys in the permssions dict are from the url path for admin screens
_area_permissions = settings.MP_ADMIN['AREA_PERMISSIONS']


class StaffAdminSite( BaseAdminSite ):
    """
    The staff admin is used by provider and sandbox staff to create and
    manage data; it is differentiated from the root admin in several ways:

     -- The staff admin is ALWAYS filtered for tenancy

     -- Its pages are embedded in the UI template framework, vs. the root
        admin which has its own UI template

     -- Subsets of feature are shown, both due to configuration of the admin
        models and by dynamic user permissions (see StaffAdminMixin)
    """

    def has_permission( self, request ):
        """
        Users must have staff privileges to access any provider/staff admin pages

        In addition, there are various modifiers on what functionality staff
        have privileges to see. The UI menu hides/shows at a fine-grain level,
        but that doesn't prevent typing in the URL.
        Some of these restrictions matter for security, some are just usability.

        HACK TESTING - test user access based on url; needs to be kept in sync with UI
        """
        if request_is_authenticated( request ):
            user = request.user
            try:
                if user.access_root:
                    log.info3("ROOT Admin: %s -> %s", request.mpipname, request.uri)
                    return True

                if user.access_staff:
                    if _check_staff_access( user, request.path ):
                        log.debug2("Admin staff: %s -> %s", request.mpname, request.uri)
                        return True

                    log.info("SUSPECT - Staff permission attempt: %s -> %s",
                                request.mpipname, request.uri)
                    if settings.MP_TESTING:
                        raise Exception('Staff permission failure')
                else:
                    log.info("SUSPECT - Non-staff admin attempt: %s -> %s",
                             request.mpipname, request.uri)
            except Exception:
                if settings.MP_TESTING:
                    raise
                log.exception("STAFF permission: %s -> %s", request.mpipname, request.uri)

    def login( self, request, _extra_context=None ):
        """
        Override admin login to redirect to portal vs Django admin login screens
        """
        return redirect_login( request )

staff_admin = StaffAdminSite( name="staff_admin" )


def _check_staff_access( user, path ):
    """
    Verify the user has rights to the admin staff url
    """

    # Path parsing of Django admin urls defined in staff.urls
    path_list = path.split('/')
    path_start = '/'.join( path_list[1:3] )
    path_area = '/'.join( path_list[3:4] )
    path_end = '/'.join( path_list[4:] )

    if path_start == settings.MP_URL_STAFF_ADMIN:

        # Don't allow staff to shorten up the url
        if not path_end or not path_area:
            return user.is_root_staff

        access_check = _area_permissions.get( path_area )
        log.debug2("Checking staff access: %s -> %s=%s", user, path_area, access_check)
        if access_check:
            method, answer = access_check

            # Special-case checks not related to user's area permissions
            if method == 'TENANT':
                if path_end.startswith('provider'):
                    return user.is_owner
                if path_end.endswith('sandbox/'):
                    return user.sees_sandboxes
            if method == 'LEVEL':
                if answer == 'SB1':
                    return user.access_high

            # Check the user's area permissions
            return not user.staff_areas or ( answer in user.staff_areas )

