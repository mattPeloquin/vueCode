#--- Mesa Platform, Copyright 2021 Vueocity, LLC
#
#   Provider changelist is only visible in the root panel
#
from django import forms
from django.urls import reverse

from mpframework.common import constants as mc
from mpframework.common.form import BaseModelForm
from mpframework.common.admin import root_admin
from mpframework.common.admin import staff_admin
from mpframework.common.admin import StaffAdminMixin
from mpframework.common.widgets import CodeEditor

from ..models.provider import Provider
from . import BaseTenantAdmin


class ProviderForm( BaseModelForm ):
    class Meta:
        model = Provider
        exclude = ()

        labels = dict( BaseModelForm.Meta.labels, **{
            })
        help_texts = dict( BaseModelForm.Meta.help_texts, **{
            'system_name': "Internal name used to identify the provider",
            'resource_path': "Path to resources under public, protected, storage - "
                    " if this changes, S3 must be updated manually",
            'isolate_sandboxes': "Turn on to prevent visibility between sites",
            })
        widgets = dict( BaseModelForm.Meta.widgets, **{
            'name': forms.TextInput( attrs=mc.UI_TEXT_SIZE_DEFAULT ),
            'street': forms.TextInput( attrs=mc.UI_TEXT_SIZE_DEFAULT ),
            'policy': CodeEditor( mode='yaml', theme='default', rows=16 ),
            'root_notes': forms.Textarea( attrs=mc.UI_TEXTAREA_LARGE ),
            })


class ProviderAdmin( BaseTenantAdmin ):
    form = ProviderForm
    list_display = ( 'system_name', 'name',  'resource_path', 'isolate_sandboxes',
                     'is_active', 'policy', 'state', 'country', 'hist_modified' )
    list_display_links = ( 'system_name', 'name' )
    list_filter = ( 'isolate_sandboxes', 'hist_created', 'hist_modified', 'is_active' )
    search_fields = ( 'name', 'system_name', 'resource_path', 'root_notes',
                      'state', 'country' )

    ordering = ( 'system_name' ,)

    fieldsets = [
        ('ROOT', {
            'mp_staff_level': 'access_root_menu',
            'classes': ('mp_collapse',),
            'fields': (
                ('system_name', 'is_active'),
                ('resource_path', 'isolate_sandboxes'),
                'policy',
                'root_notes',
                )
            }),
        ("Information", {
            'classes': ('mp_collapse',),
            'fields': (
                'name',
                'street',
                ('city', 'state'),
                ('country', 'postal_code'),
                ('phone', 'phone2'),
                )
            }),
        ]

    def has_add_permission( self, request ):
        # Only allow adding from root change list (provider changelist never visible)
        return request.path.startswith(
                    reverse( 'root_admin:tenant_provider_changelist' ) )

root_admin.register( Provider, ProviderAdmin )

#--------------------------------------------------------------------

class ProviderStaffAdmin( StaffAdminMixin, ProviderAdmin ):
    see_changelist = False
    can_add_item = False

staff_admin.register( Provider, ProviderStaffAdmin )
