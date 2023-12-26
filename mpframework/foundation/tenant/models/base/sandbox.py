#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Base class for sandbox models
"""
from django.db import models

from mpframework.common.cache import stash_method_rv
from mpframework.common.model import BaseModel

from .tenant_clone import TenantCloneMixin


class SandboxModel( TenantCloneMixin, BaseModel ):
    """
    Base class for models partitioned on sandboxes
    """
    sandbox = models.ForeignKey( 'tenant.Sandbox', models.CASCADE,
                verbose_name=u"Site" )

    class Meta:
        abstract = True

    # Used to manage shared tenant functionality
    _tenancy_type = 'sandbox'

    @property
    @stash_method_rv
    def public_storage_path( self ):
        # By default sandbox models place all uploaded public content in
        # one location under the provider
        return self.sandbox.public_storage_path
