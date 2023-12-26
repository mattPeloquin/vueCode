#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    PayEvent admin
"""

from mpframework.common.admin import root_admin
from mpframework.common.admin import staff_admin
from mpframework.common.admin import StaffAdminMixin
from mpframework.common.form import BaseModelForm
from mpframework.common.widgets import CodeEditor
from mpframework.foundation.tenant.admin import BaseTenantAdmin

from ..models import PayEvent


class PayEventForm( BaseModelForm ):
    class Meta:
        model = PayEvent
        exclude = ()

        labels = dict( BaseModelForm.Meta.labels, **{
            })
        help_texts = dict( BaseModelForm.Meta.help_texts, **{
            })
        widgets = dict( BaseModelForm.Meta.widgets, **{
            'history': CodeEditor( mode='yaml', theme='default', rows=12 ),
            })


class PayEventAdmin( BaseTenantAdmin ):
    form = PayEventForm

    list_display = ( 'pay_using','pay_to', 'apa', 'hist_modified',
            ) + BaseTenantAdmin.list_display

    search_fields = ( 'apa__account__name' ,)

    readonly_fields = ( 'pay_using','pay_to', 'apa'
            ) + BaseTenantAdmin.readonly_fields

    fieldsets = [
        ("", {
            'classes': ('mp_collapse',),
            'fields': (
                ('pay_using','pay_to'),
                'apa',
                'history',
                ('hist_created', 'hist_modified'),
                )
            }),
        ('ROOT', {
            'classes': ('mp_collapse',),
            'mp_staff_level': 'access_root_menu',
            'fields': (
                )
            }),
        ]

root_admin.register( PayEvent, PayEventAdmin )


class PayEventStaffAdmin( StaffAdminMixin, PayEventAdmin ):
    can_add_item = False

staff_admin.register( PayEvent, PayEventStaffAdmin )
