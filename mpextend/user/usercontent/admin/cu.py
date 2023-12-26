#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Sudent admin screens
"""
from django.db.models import Count

from mpframework.common.admin import root_admin
from mpframework.foundation.tenant.admin import BaseTenantAdmin
from mpframework.foundation.tenant.admin import TabularInlineView

from ..models import UserItem
from ..models import ContentUser


class UserContentItemInline( TabularInlineView ):
    model = UserItem

    fields = ( 'item', 'progress', 'uses', 'seconds_used',
               'hist_created', 'completed', 'feedback')
    readonly_fields = ('item',)
    ordering = ('item',)


class UserContentInline( TabularInlineView ):
    model = ContentUser
    inlines = ( UserContentItemInline ,)

    fieldsets = [
        ("Items", {
            'classes': ('mp_placeholder useritem_set-group',),
            'fields' : (),
            }),
        ]

    def item_usage( self, instance ):
        return instance
    item_usage.short_description = ""


class ContentUserAdmin( BaseTenantAdmin ):
    inlines = ( UserContentItemInline ,)
    list_display = ( '__str__', 'sandbox', 'cui_count' )
    search_fields = ( 'user__email' ,)
    readonly_fields = ( 'user' ,)

    fieldsets = [
        ("Items", {
            'classes': ('mp_placeholder useritem_set-group',),
            'fields' : (),
            }),
        ("ROOT", {
            'mp_staff_level': 'access_root_menu',
            'classes': ('mp_collapse mp_closed',),
            'fields': (
                'user',
                'sandbox',
                )
            }),
        ]

    def get_queryset( self, request ):
        qs = super().get_queryset( request )
        qs = qs.annotate(
                cui_count = Count( 'items', distinct=True ),
                )
        return qs

    def cui_count( self, obj ):
        return obj.cui_count if obj.cui_count else ""
    cui_count.short_description = 'Items'
    cui_count.admin_order_field = 'cui_count'

root_admin.register( ContentUser, ContentUserAdmin )
