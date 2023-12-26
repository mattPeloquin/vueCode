#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Tenant admin screens and base classes
"""

from .base_inline import ExtendInlineView
from .base_inline import TabularInlineBase
from .base_inline import TabularInlineView
from .base_inline import TabularInlineNoTenancy
from .base_provider_optional import ProviderOptionalAdminMixin
from .base_model import BaseTenantAdmin

# Imports to make admin screens available through autodiscover
from .provider import *
from .sandbox import *
from .host import *
