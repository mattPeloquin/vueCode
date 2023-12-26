#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Account admin screen with embedded GroupAccount that
    is shown as the "GroupAccount" screen
"""
from django import forms
from django.db.models import Count

from mpframework.common import constants as mc
from mpframework.common.form import BaseModelForm
from mpframework.common.admin import root_admin
from mpframework.common.admin import staff_admin
from mpframework.common.admin import StaffAdminMixin
from mpframework.common.admin import mpListFilter
from mpframework.foundation.tenant.admin import BaseTenantAdmin
from mpframework.foundation.tenant.admin import TabularInlineView
from mpextend.product.catalog.models import PA

from ..models import Account
from ..models import AccountUser
from ..models import APA


class AccountForm( BaseModelForm ):
    class Meta:
        model = Account
        exclude = ()

        labels = dict( BaseModelForm.Meta.labels, **{
            'name': "Account name",
            'pas': "Pricing options used",
            'codes': "Account codes",
            })

        help_texts = dict( BaseModelForm.Meta.help_texts, **{
            'name': "Name of account (this can be modified by the account admin)",
            'status': "Retired accounts cannot make new purchases<br>"
                    "Suspended accounts cannot use existing licenses",
            'codes': "Custom codes used to match accounts to special pricing "
                    "options (comma-delimited)",
            })

        widgets = dict( BaseModelForm.Meta.widgets, **{
            'name': forms.TextInput( attrs=mc.UI_TEXT_SIZE_DEFAULT ),
            'street': forms.TextInput( attrs=mc.UI_TEXT_SIZE_LARGE ),
            })


class PrimaryUsersInline( TabularInlineView ):
    model = AccountUser
    fields = ( 'user' ,)
    readonly_fields = fields
    verbose_name_plural = u"Primary Account Users"

class APAInline( TabularInlineView ):
    model = APA
    fields = ( 'pa', '_is_active', 'ga_users_max', 'period_end', 'id' )
    readonly_fields = fields

PAsFilter = mpListFilter.new( PA, u"Pricing option", 'pa_id' )


class AccountAdmin( BaseTenantAdmin ):
    form = AccountForm
    inlines = ( PrimaryUsersInline, APAInline )

    list_display = ( 'name', 'status', 'user_count', 'pa_count', 'codes',
            'hist_created' )

    list_filter = ( 'status', PAsFilter )
    search_fields = ( 'name', 'city', 'state', 'country', 'postal_code' )
    readonly_fields = ( 'group_account' ,)

    fieldsets = [
        ("", {
            'classes': ('mp_collapse',),
            'fields': (
                'name',
                'group_account',
                ('status', 'codes'),
                )
            }),
        ("Users", {
            'classes': ('mp_placeholder primary_aus-group',),
            'fields' : (),
            }),
        ("Licenses", {
            'classes': ('mp_placeholder apas-group',),
            'fields' : (),
            }),
        ("Contact information", {
            'classes': ('mp_collapse',),
            'fields': (
                'street',
                ('city', 'state'),
                ('country', 'postal_code'),
                ('phone', 'phone2'),
                )
            }),
        ("ROOT", {
            'classes': ('mp_collapse mp_closed',),
            'mp_staff_level': 'access_root_menu',
            'fields': (
                'sandbox',
                ('hist_created', 'hist_modified'),
                )
            }),
        ]

    # Add aggregate counts to queryset for use in admin display
    def get_queryset( self, request ):
        qs = super().get_queryset( request )
        return qs.annotate(
            pa_count = Count('pas', distinct=True),
            user_count = Count( 'group_account__users', distinct=True ),
            )

    def pa_count( self, obj ):
        return obj.pa_count
    pa_count.short_description = "Pricing options"
    pa_count.admin_order_field = 'pa_count'

    def user_count( self, obj ):
        if obj.is_group:
            return obj.user_count
        else:
            return ''
    user_count.short_description = "Users"
    user_count.admin_order_field = 'user_count'

root_admin.register( Account, AccountAdmin )


class AccountStaffAdmin( StaffAdminMixin, AccountAdmin ):
    """
    REGISTER FOR AUTOLOOKUP
    There isn't an account staff admin screen, but need to register staff admin
    for the account base class so it can be used in autolookup selection.
    """
    pass

staff_admin.register( Account, AccountStaffAdmin )
