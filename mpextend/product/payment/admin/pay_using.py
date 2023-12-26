#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    PayUsing admin
"""

from mpframework.common.admin import root_admin
from mpframework.common.admin import staff_admin
from mpframework.common.admin import StaffAdminMixin
from mpframework.common.form import BaseModelForm
from mpframework.common.widgets import CodeEditor
from mpframework.foundation.tenant.admin import BaseTenantAdmin
from mpextend.product.account.models import Account

from ..models import PayUsing
from .pay_mixin import PayAdminMixin


class PayUsingForm( BaseModelForm ):
    class Meta:
        model = PayUsing
        exclude = ()

        labels = dict( BaseModelForm.Meta.labels, **{
            '_apa_payments': "User payment info",
            })
        help_texts = dict( BaseModelForm.Meta.help_texts, **{
            '_apa_payments': "Holds users that have made payments with "
                "the payment_type for this account.",
            })
        widgets = dict( BaseModelForm.Meta.widgets, **{
            '_apa_payments': CodeEditor( mode='yaml', theme='default', rows=12 ),
            })


class PayUsingAdmin( BaseTenantAdmin, PayAdminMixin ):
    form = PayUsingForm

    list_display = ( 'account','pay_to','hist_modified',
            ) + BaseTenantAdmin.list_display

    search_fields = ( 'account__name' ,)

    readonly_fields = ( 'account','pay_to'
            ) + BaseTenantAdmin.readonly_fields

    filter_fk = {
            'account': ( Account.objects, 'SANDBOX' ),
             }

    fieldsets = [
        ("", {
            'classes': ('mp_collapse',),
            'fields': (
                ('account','pay_to'),
                '_apa_payments',
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

root_admin.register( PayUsing, PayUsingAdmin )


class PayToStaffAdmin( StaffAdminMixin, PayUsingAdmin ):
    can_add_item = False

staff_admin.register( PayUsing, PayToStaffAdmin )
