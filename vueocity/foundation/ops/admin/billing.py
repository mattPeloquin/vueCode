#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Provider billing admin
"""
from mpframework.common.form import BaseModelForm
from mpframework.common.admin import root_admin
from mpframework.common.admin import staff_admin
from mpframework.common.admin import StaffAdminMixin
from mpframework.foundation.tenant.admin import BaseTenantAdmin

from ..models import Invoice


class InvoiceForm( BaseModelForm ):
    class Meta:
        model = Invoice
        exclude = ()


class InvoiceAdmin( BaseTenantAdmin ):
    form = InvoiceForm

    list_display = ( 'state', 'amount', 'tax', 'external_id' )
    search_fields = ( 'description' ,)

    fieldsets = [
        ('', {
            'classes': ('mp_collapse',),
            'fields': (
                'state',
                'description',
                ('amount', 'tax'),
                ('date_sent', 'date_paid'),
                'external_id',
                'history',
                )
            }),
        ('ROOT', {
            'mp_staff_level': 'access_root_menu',
            'classes': ('mp_collapse mp_closed',),
            'fields': (
                '_provider',
                )
            }),
        ]

root_admin.register( Invoice, InvoiceAdmin )


class InvoiceStaffAdmin( StaffAdminMixin, InvoiceAdmin ):
    pass

staff_admin.register( Invoice, InvoiceStaffAdmin )

