#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Root only Account admin screens
"""
from django.db.models import Q

from mpframework.common.admin import root_admin
from mpframework.foundation.tenant.admin import BaseTenantAdmin
from mpframework.foundation.tenant.admin import TabularInlineNoTenancy

from ..models import AccountUser
from ..models import Account
from ..models import GroupAccount


class GroupAccountsInline( TabularInlineNoTenancy ):
    model = GroupAccount.users.through
    fields = ( 'groupaccount' ,)
    readonly_fields = fields
    verbose_name_plural = u"Group Accounts"
    classes = ( 'mp_collapse' ,)
    can_delete = False
    max_num = 0


class AccountUserAdmin( BaseTenantAdmin ):
    inlines = ( GroupAccountsInline ,)
    search_fields = ( 'user__email', 'primary_account__name',
                'ga_accounts__base_account__name' )
    readonly_fields = ('user', 'sandbox')

    fieldsets = [
        ('ROOT', {
            'mp_staff_level': 'access_root_menu',
            'classes': ('mp_collapse',),
            'fields': (
                'sandbox',
                'user',
                'primary_account',
                )
            }),
        ( GroupAccountsInline, {
            'classes': ('mp_placeholder ga_accounts-group',),
            'fields' : (),
            }),
        ]

    def formfield_for_foreignkey( self, db_field, request, **kwargs ):
        """
        Limit selections user; both for practical purpose and
        because Django will timeout creating large numbers of objects
        """
        if db_field.name == 'primary_account':
            au = request.mpstash['admin_obj']
            args = ( Q( primary_aus=au.pk ) |
                      Q( group_account__users=au.pk ) ,)
            kwargs['queryset'] = Account.objects.filter( *args ).distinct()

        return super().formfield_for_foreignkey( db_field, request, **kwargs )

root_admin.register( AccountUser, AccountUserAdmin )
