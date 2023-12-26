#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    User Admin objects
    Place these imports here to make admin screens available through autodiscover
"""

from .user import mpUserRootAdmin
from .user import mpUserStaffAdmin_All
from .user import mpUserStaffAdmin_Customers
from .user import mpUserStaffAdmin_Staff

from .other import PermissionAdmin
from .other import AuthGroupAdmin
