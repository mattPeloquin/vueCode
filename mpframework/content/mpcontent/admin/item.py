#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Polymorphic Content Item admin
"""

from mpframework.common.admin import staff_admin
from mpframework.common.admin import StaffAdminMixin
from mpframework.common.admin import BaseChangeList

from ..models import BaseItem
from . import BaseItemAdmin


class ItemChangeList( BaseChangeList ):
    """
    Make some items in content changelist polymorphic
    """

    def url_for_result( self, result ):
        """
        Since we know URLs will always follow same format, just swap
        the base class edit url with the downcast one
        """
        url = super().url_for_result( result )
        url = url.replace( '/mpcontent/baseitem/',
                           '/mpcontent/{}/'.format( result.downcast_model_name ) )
        return url


class ItemStaffAdmin( StaffAdminMixin, BaseItemAdmin ):
    """
    Show all non-collection content for the sandbox
    """

    list_display = ( '_name', 'tag', 'ctype', 'workflow'
            ) + BaseItemAdmin.LIST_END
    list_filter =  BaseItemAdmin.list_filter

    def __init__( self, *args, **kwargs ):
        super().__init__( *args, **kwargs )
        self.ld_insert_pos = 4

    def get_changelist( self, request, **kwargs ):
        return ItemChangeList

    def get_queryset( self, request ):
        qs = super().get_queryset( request )
        qs = qs.exclude( _django_ctype__model__startswith='tree' )
        return qs

    def ctype( self, obj ):
        return obj.type_name
    ctype.short_description = "Content type"
    ctype.admin_order_field = '_django_ctype'

staff_admin.register( BaseItem, ItemStaffAdmin )
