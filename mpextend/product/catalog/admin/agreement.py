#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Admin screens for agreement models
"""

from mpframework.common.form import BaseModelForm
from mpframework.common.admin import root_admin
from mpframework.common.admin import staff_admin
from mpframework.common.admin import StaffAdminMixin
from mpframework.common.admin import mpListFilter
from mpframework.common.widgets import CodeEditor
from mpframework.foundation.tenant.admin import BaseTenantAdmin
from mpframework.foundation.tenant.admin import ProviderOptionalAdminMixin

from ..models.agreement import Agreement


class AgreementForm( BaseModelForm ):
    class Meta:
        model = Agreement
        exclude = ()

        labels = dict( BaseModelForm.Meta.labels, **{
            'rules': "License rules",
            'order': "Display order",
            })
        help_texts = dict( BaseModelForm.Meta.help_texts, **{
            'name': "Describe the license type",
            'order': "Optionally define alphabetical or numerical order "
                    "for displaying license types.",
            'rules': "Define the license rules that provide a template for "
                    "pricing options.<br>"
                    "{help_license_rules}",
            })
        widgets = dict( BaseModelForm.Meta.widgets, **{
            'rules': CodeEditor( mode='yaml', theme='default', rows=12 ),
            })


class ActiveFilter( mpListFilter ):
    title = "State"
    parameter_name = 'state'
    def lookups( self, request, model_admin ):
        return [ ( 'active', "Active" ),
                 ( 'inactive', "Inactive" ),
                 ]
    def queryset( self, request, qs ):
        query = Agreement.is_active_Q()
        if self.value() == 'active':
            return qs.filter( query ).distinct()
        if self.value() == 'inactive':
            return qs.exclude( query ).distinct()


class AgreementAdmin( ProviderOptionalAdminMixin, BaseTenantAdmin ):
    form = AgreementForm

    list_display = ( 'provider_item', 'name', 'enabled', 'notes',
            'order', 'rules' )
    list_editable = ( 'order' ,)
    list_display_links = ( 'name' ,)

    ordering = ( '-provider_optional', 'order', 'name' )

    list_filter = [ ActiveFilter, 'hist_modified', 'hist_created' ]
    list_filter_options = {
        'ActiveFilter': { 'default': 'active' },
        }

    search_fields = ( 'name', 'notes', 'rules' )

    fieldsets = [
        ('', {
            'classes': ('mp_collapse',),
            'fields': (
                ('name', 'enabled'),
                ('notes', 'order'),
                'rules',
                )
            }),
        ('ROOT', {
            'mp_staff_level': 'access_root_menu',
            'classes': ('mp_collapse mp_closed',),
            'fields': (
                'provider_optional',
                )
            }),
        ]

root_admin.register( Agreement, AgreementAdmin )


class AgreementStaffAdmin( StaffAdminMixin, AgreementAdmin ):
    pass

staff_admin.register( Agreement, AgreementStaffAdmin )

