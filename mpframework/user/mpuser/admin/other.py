#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Provide root access to Django DB permissions
"""
from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.auth.models import Group as AuthGroup
from django.contrib.auth.admin import GroupAdmin as AuthGroupAdminBase

from mpframework.common.admin import root_admin
from mpframework.common.admin import BaseAdmin


class PermissionAdmin( BaseAdmin ):
    no_tenant_filter = True
    list_display = ( 'name', 'content_type', 'codename' )
    list_add_root = ()


class AuthGroupAdmin( AuthGroupAdminBase ):
    list_display = ( 'id', 'name' )


# At this point these are NOT being used, so access is debug only
if settings.DEBUG:

    root_admin.register( Permission, PermissionAdmin )
    root_admin.register( AuthGroup, AuthGroupAdmin )
