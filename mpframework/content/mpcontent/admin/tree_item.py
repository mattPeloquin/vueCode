#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Inline for adding items to tree nodes
"""
from django.forms.widgets import HiddenInput

from mpframework.common.admin import root_admin
from mpframework.common.admin import BaseAdmin
from mpframework.common.form import BaseModelForm
from mpframework.foundation.tenant.admin import TabularInlineNoTenancy

from ..models import BaseItem
from ..models import TreeBaseItem


class TreeItemAdminInlineForm( BaseModelForm ):
    autolookup_fields = ('item',)
    original = False
    show_url = True


class TreeItemAdminInline( TabularInlineNoTenancy ):
    model = TreeBaseItem
    form = TreeItemAdminInlineForm
    verbose_name = u"Item"
    verbose_name_plural = u"Content items"

    fields = ( 'area', 'item', 'is_required', 'item_workflow',
                'item_size', 'item_points', 'drag_order' )
    readonly_fields = ( 'item_workflow', 'item_size', 'item_points' )

    sortable_field_name = 'drag_order'
    ordering = ( 'area', 'drag_order', 'item__tag' )

    fk_name = 'tree'
    filter_fk = {
            'item': ( BaseItem.objects, 'SANDBOX' ),
             }

    def get_queryset( self, request ):
        qs = super().get_queryset( request )
        qs = qs.filter( request=request ).exclude( item__workflow__in='R' )
        return qs

    def formfield_for_dbfield( self, db_field, **kwargs ):
        if db_field.name == self.sortable_field_name:
            kwargs["widget"] = HiddenInput()
        return super().formfield_for_dbfield( db_field, **kwargs )

    def item_workflow( self, obj ):
        return obj.item.get_workflow_display()
    item_workflow.short_description = "Workflow"

    def item_size( self, obj ):
        return obj.item.size if obj.item.size else ''
    item_size.short_description = "Size"

    def item_points( self, obj ):
        return obj.item.points if obj.item.points else '1'
    item_points.short_description = "Points"


class TreeBaseItemAdmin( BaseAdmin ):
    """
    Provide root access to the Tree MTM through table
    """
    no_tenant_filter = True
    ordering = ( 'tree', 'item__tag' ,)

    list_display = ( 'tree', 'area', 'item', 'is_required', 'drag_order' )
    list_editable = ( 'is_required', 'drag_order' )

root_admin.register( TreeBaseItem, TreeBaseItemAdmin )
