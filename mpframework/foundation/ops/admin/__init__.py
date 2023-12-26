#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    mpFramework Ops admin
"""

# Patches
from .disable_sort import *

# Convenience imports
from .field_change_mixin import FieldChangeMixin

# Imports to make admin screens available through autodiscover
from .field_change import FieldChangeStaffAdmin
from .health_check import HealthCheckRootAdmin

# Non-framework tables
from ._django import LogEntryAdmin
from ._django import ContentTypeAdmin
