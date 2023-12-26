#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Framework inlines with defaults and tenant filtering support
"""
from django.conf import settings
from nested_admin import NestedTabularInline

from mpframework.common.admin.base_mixin import AdminSharedMixin

from .base_mixin import TenantAdminMixin


class _BaseInlineMixin( AdminSharedMixin, NestedTabularInline ):
    """
    Add MPF admin code to NestedAdmin
    """
    extra = 0

class TabularInlineNoTenancy( _BaseInlineMixin ):
    pass

class TabularInlineBase( TenantAdminMixin, TabularInlineNoTenancy ):
    pass

class TabularInlineView( TabularInlineBase ):
    can_delete = False
    max_num = 0

# Extend inline view makes single inline instance appear as part of panel

class ExtendInlineView( _BaseInlineMixin ):
    template = 'admin/_/extend_inline.html'
    can_delete = False
    min_num = 1
    max_num = 1
