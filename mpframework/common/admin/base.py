#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Bases for Admin classes
"""
from django.contrib.admin import AdminSite
from django.contrib.admin.sites import AlreadyRegistered

from .. import log


# Sidebar not used in MPF, and causes warnings
AdminSite.enable_nav_sidebar = False


class BaseAdminSite( AdminSite ):
    """
    Used for all admin sites in the system
    """

    def register( self, *args, **kwargs ):
        """
        Wrap the register method to avoid blowup with multiple registrations
        """
        try:
            super().register( *args, **kwargs )
        except AlreadyRegistered:
            log.exception("Admin Registration exception for: %s -- ignoring", args[1])
