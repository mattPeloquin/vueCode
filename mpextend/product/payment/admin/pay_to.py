#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    PayTo admin
"""

from mpframework.common.admin import root_admin
from mpframework.common.admin import staff_admin
from mpframework.common.admin import StaffAdminMixin
from mpframework.common.form import BaseModelForm
from mpframework.common.widgets import CodeEditor
from mpframework.foundation.tenant.admin import BaseTenantAdmin
from mpextend.product.account.models import GroupAccount

from ..models import PayTo
from .pay_mixin import PayAdminMixin


class PayToForm( BaseModelForm ):
    class Meta:
        model = PayTo
        exclude = ()

        labels = dict( BaseModelForm.Meta.labels, **{
            'service_account': "Account ID",
            'payment_config': "Configuration",
            'select_order': "Priority",
            })
        help_texts = dict( BaseModelForm.Meta.help_texts, **{
            'service_account': "The external service's ID for this account",
            'payment_config': "Holds configuration data for the payment.",
            })
        widgets = dict( BaseModelForm.Meta.widgets, **{
            'payment_config': CodeEditor( mode='yaml', theme='default', rows=12 ),
            })


class PayToAdmin( BaseTenantAdmin, PayAdminMixin ):
    form = PayToForm

    list_display = ( 'sandbox', 'payment_type', 'service_account', 'hist_modified' )

    search_fields = ( 'service_account', 'seller_account__name' ,)

    root_edit_fields = ( 'sandbox', 'seller_account' )

    filter_fk = {
            'seller_account': ( GroupAccount.objects, 'SANDBOX' ),
             }

    fieldsets = [
        ("", {
            'classes': ('mp_collapse',),
            'fields': (
                'service_account',
                'payment_config',
                ('hist_created', 'hist_modified'),
                )
            }),
        ('ROOT', {
            'classes': ('mp_collapse',),
            'mp_staff_level': 'access_root_menu',
            'fields': (
                'payment_type',
                '_provider',
                'sandbox',
                'seller_account',
                )
            }),
        ]

root_admin.register( PayTo, PayToAdmin )


class PayToStaffAdmin( StaffAdminMixin, PayToAdmin ):
    can_add_item = False

staff_admin.register( PayTo, PayToStaffAdmin )
