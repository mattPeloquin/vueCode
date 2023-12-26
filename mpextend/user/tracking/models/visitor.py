#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Visitor tracking
"""
from django.db import models

from mpframework.foundation.tenant.models.base import TenantManager
from mpframework.foundation.tenant.models.base import SandboxModel

from .tracking_base import BaseTracking


class VisitorTracking( BaseTracking, SandboxModel ):
    """
    Data and logic for user and visitor tracking
    """

    objects = TenantManager()

    requests = models.IntegerField( db_index=True, default=0 )

    def __str__(self):
        # Only directly visible in root/debug/log
        return str( self.ip_address )
