#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Content user admin
"""
from django import forms
from django.contrib.contenttypes.models import ContentType

from mpframework.common import constants as mc
from mpframework.common.form import BaseModelForm
from mpframework.common.admin import root_admin
from mpframework.common.admin import staff_admin
from mpframework.common.admin import StaffAdminMixin
from mpframework.common.admin import mpListFilter
from mpframework.common.admin.large import AdminLargeMixin
from mpframework.foundation.tenant.admin import BaseTenantAdmin
from mpframework.content.mpcontent.models import get_content_item_types

from ..models import UserItem


class UserItemForm( BaseModelForm ):
    class Meta:
        model = UserItem
        exclude = ()

        labels = dict( BaseModelForm.Meta.labels, **{
            'progress_data': "Progress data",
            'hist_created': "Started",
            })
        help_texts = dict( BaseModelForm.Meta.help_texts, **{
            'progress_data': "Data storing the state of content, setting to blank resets.",
            })
        widgets = dict( BaseModelForm.Meta.widgets, **{
            'feedback_data': forms.Textarea( attrs=mc.UI_TEXTAREA_LARGE ),
            'progress_data': forms.Textarea( attrs=mc.UI_TEXTAREA_LARGE ),
            })

class TypeFilter( mpListFilter ):
    """
    Filter by MPF content groups
    """
    title = "Content type"
    parameter_name = 'itemtype'
    def lookups( self, request, model_admin ):
        return [ (ct, ct.capitalize() + "s") for ct in get_content_item_types() ]
    def queryset( self, request, qs ):
        if self.value():
            return qs.filter( item___django_ctype__model=self.value() )

class BaseUserItemAdmin( BaseTenantAdmin ):
    form = UserItemForm
    list_display = ('cu', 'item', 'purchase_type', 'item_type', 'top_tree',
                     'progress', 'uses', 'minutes', 'feedback', 'last_used')
    list_display_links = ('cu',)
    list_editable = ('progress',)
    list_filter = ( TypeFilter, 'progress', 'feedback', 'last_used', 'hist_created')
    list_text_small = ('item', 'last_used') + BaseTenantAdmin.list_text_small
    list_col_med = ('item', 'last_used') + BaseTenantAdmin.list_text_small
    search_fields = ( 'cu__user__email', 'cu__user__first_name', 'cu__user__last_name',
                      'apa__custom_name',
                      'item__tag', 'item__internal_tags', 'item___name',
                      'top_tree__item__tag', 'top_tree__item__internal_tags',
                      'top_tree__item___name' )
    ordering = ( '-last_used' ,)
    readonly_fields = BaseTenantAdmin.readonly_fields + (
                        'cu', 'item', 'top_tree', 'apa' )
    fieldsets = [
        ('', {
            'fields': (
                ('cu', 'item'),
                'top_tree',
                ('progress', 'apa'),
                ('uses', 'seconds_used'),
                ('hist_created', 'last_used'),
                ('completed', 'feedback'),
                ),
            }),
        ("Admin", {
            'mp_staff_level': 'access_high',
            'classes': ('mp_collapse mp_closed',),
            'fields': (
                'hist_modified',
                'feedback_state',
                'feedback_data',
                'progress_data',
                ),
            }),
        ('ROOT', {
            'mp_staff_level': 'access_root_menu',
            'classes': ('mp_collapse mp_closed',),
            'fields': (
                'item_version',
                )
            }),
        ]

    def get_queryset( self, request ):
        qs = super().get_queryset( request )
        # Hide uninitialized change requests in most cases
        if not request.user.logged_into_root:
            qs = qs.exclude( uses=0 )
        return qs

    def item_type( self, obj ):
        return obj and obj.item._django_ctype
    item_type.short_description = "Type"
    item_type.admin_order_field = 'item___django_ctype'

    def purchase_type( self, obj ):
        return obj and obj.apa and obj.apa.get_purchase_type_display()
    purchase_type.short_description = "Purchase"
    purchase_type.admin_order_field = 'apa__purchase_type'

    def minutes( self, obj ):
        return obj.minutes_used
    minutes.short_description = 'Minutes'
    minutes.admin_order_field = 'seconds_used'


class UserItemStaffAdmin( StaffAdminMixin, AdminLargeMixin, BaseUserItemAdmin ):
    can_add_item = False
    list_display = ( 'cu', 'item', 'purchase_type', 'item_type', 'top_tree',
                     'progress', 'uses', 'minutes', 'feedback',
                     'last_used' )
    list_text_small = ('top_tree',) + BaseUserItemAdmin.list_text_small

    def get_queryset( self, request ):
        qs = super().get_queryset( request )
        tree_type = ContentType.objects.get_by_natural_key( 'mpcontent', 'tree' )
        return qs.exclude( item___django_ctype_id=tree_type.pk )

staff_admin.register( UserItem, UserItemStaffAdmin )


class UserItemStaffTreeAdmin( StaffAdminMixin, AdminLargeMixin, BaseUserItemAdmin ):
    can_add_item = False

    list_display = ( 'cu', 'item', 'progress', 'uses', 'minutes', 'feedback',
                     'last_used' )

    def get_queryset( self, request ):
        qs = super().get_queryset( request )
        tree_type = ContentType.objects.get_by_natural_key( 'mpcontent', 'tree' )
        return qs.filter( item___django_ctype_id=tree_type.pk, top_tree__isnull=True )

class UserItemTop( UserItem ):
    class Meta:
        proxy = True
        verbose_name = u"Collection Usage"

staff_admin.register( UserItemTop, UserItemStaffTreeAdmin )


class UserItemRootAdmin( AdminLargeMixin, BaseUserItemAdmin ):

    list_display = ( 'cu', 'item', 'purchase_type', 'item_type', 'top_tree',
                     'progress', 'uses', 'seconds_used',
                     'feedback',  'feedback_state', 'item_version' )
    list_editable = ( 'progress', 'uses', 'seconds_used', 'feedback', 'feedback_state' )

    list_per_page = BaseUserItemAdmin.list_per_page * 2

root_admin.register( UserItem, UserItemRootAdmin )
