#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Staff screens for view history changes
"""
from django import forms

from mpframework.common import constants as mc
from mpframework.common.form import BaseModelForm
from mpframework.common.admin import root_admin
from mpframework.common.admin import staff_admin
from mpframework.common.admin import StaffAdminMixin
from mpframework.foundation.tenant.admin import BaseTenantAdmin

from ..models.field_change import FieldChange


class FieldChangeForm( BaseModelForm ):
    class Meta:
        model = FieldChange
        exclude = ()

        labels = dict( BaseModelForm.Meta.labels, **{
           'value': "Previous value"
            })

        help_texts = dict( BaseModelForm.Meta.help_texts, **{
            })

        widgets = dict( BaseModelForm.Meta.widgets, **{
            'value': forms.Textarea( attrs={'rows': 24, 'cols': mc.CHAR_LEN_UI_LINE} ),
            })


class FieldChangeAdmin( BaseTenantAdmin ):
    form = FieldChangeForm

    list_display_links = ( 'user' ,)
    search_fields = ( 'user__email', 'field' )

    fieldsets = [
        ('', {
            'classes': ('mp_collapse',),
            'fields': (
                ('user', 'hist_modified'),
                'desc',
                'value',
                )
            }),
        ('ROOT', {
            'mp_staff_level': 'access_root_menu',
            'classes': ('mp_collapse mp_closed',),
            'fields': (
                ('sandbox'),
                ('field', 'hist_created'),
                ('ctype', 'object_id'),
                )
            }),
        ]


class FieldChangeRootAdmin( FieldChangeAdmin ):
    list_display = ( 'sandbox', 'user', 'ctype', 'field',
                     'desc', 'hist_modified' )
    list_filter = ( 'sandbox', 'ctype' )

root_admin.register( FieldChange, FieldChangeRootAdmin )


class FieldChangeStaffAdmin( StaffAdminMixin, FieldChangeAdmin ):
    list_display = ( 'user', 'ctype', 'desc', 'hist_created' )
    readonly_fields = list_display
    can_add_item = False

staff_admin.register( FieldChange, FieldChangeStaffAdmin )

