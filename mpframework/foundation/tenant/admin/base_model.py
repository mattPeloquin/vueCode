#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Base admin class for MPF tenant models
"""

from mpframework.common.admin import BaseModelAdmin

from .base_mixin import TenantAdminMixin


class BaseTenantAdmin( TenantAdminMixin, BaseModelAdmin ):
    """
    This is the admin base for most models in the system.
    There are various other model admin scenarios that
    use portions of shared admin code; this pulls all of
    them together.
    """
    pass
