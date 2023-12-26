#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Support for GroupAccount admin
    GAs assume they are only visible in BV1 and above
"""
from django.db.models import Count

from mpframework.common import log
from mpframework.common import _
from mpframework.common import constants as mc
from mpframework.common.delivery import DELIVERY_MODES_ALL, DELIVERY_MODES_STAFF
from mpframework.common.form import BaseModelForm
from mpframework.common.admin import root_admin
from mpframework.common.admin import staff_admin
from mpframework.common.admin import StaffAdminMixin
from mpframework.common.widgets import CodeEditor
from mpframework.foundation.tenant.admin import BaseTenantAdmin
from mpframework.foundation.tenant.admin import ExtendInlineView

from ..models import Account
from ..models import GroupAccount
from .account import AccountForm
from .au_mixin import AccountUsersFields


class GroupAccountForm( BaseModelForm ):
    """
    Form used for both Account GA inline, and root GA form
    """
    autolookup_fields = ('users',)
    class Meta:
        model = GroupAccount
        exclude = ()

        labels = dict( BaseModelForm.Meta.labels, **{
            'users': "Add users to account",
            'admins': "Add account admins",
            'delivery_mode': "Content protection level",
            'beta_access': "Beta access",
            'extended_access': "Extended content access",
            'invite_code': "Invite code",
            'notify_level': "Notification level",
            })
        help_texts = dict( BaseModelForm.Meta.help_texts, **{
            'invite_code': "Invitation code users enter to join the group.<br>"
                    "If blank, users can only be invited via emails by a group admin.",
            'delivery_mode': "Override content protection level to resolve problems "
                    "accessing content in some user networks",
            'beta_access': "Allow all members of this account to see all Beta content",
            'extended_access': "Allow all members of this account to see content "
                    "marked as extended access.",
            'notify_level': "Select the frequency of emails sent to admins on events such "
                    "as adding/removing users, adding licenses, content usage, etc.",
            'external_key': "Optional ID, key, etc. to tie account to external "
                    "system such as Salesforce (admins do not see)",
            'external_group': "Optional names/codes added to account for reporting "
                    "and/or connecting to external systems (admins do not see)",
            'admins': "If you've added users to the account, you'll need to save "
                    "before they can be added as an admin",
            })
        widgets = dict( BaseModelForm.Meta.widgets, **{
            'options': CodeEditor( mode='yaml', theme='default', rows=12 ),
            })

    def __init__( self, *args, **kwargs ):
        super().__init__( *args, **kwargs )

        # Allow override with more specialized modes
        if self.fields.get('delivery_mode'):
            if self.user and self.user.access_root:
                self.fields['delivery_mode'].choices = DELIVERY_MODES_ALL
            else:
                self.fields['delivery_mode'].choices = DELIVERY_MODES_STAFF

#--------------------------------------------------------------------

class AccountInline( ExtendInlineView ):
    # Place account model information inline on the GA form
    form = AccountForm
    model = Account

    fieldsets = [
        ('', {
            'classes': ('mp_collapse',),
            'fields': (
                'name',
                ('status', 'codes'),
                )
            }),
        ]

class AccountInline2( ExtendInlineView ):
    # This will be placed at the end of groups, since it is
    # not in fieldset because it shares model name with above
    form = AccountForm
    model = Account

    fieldsets = [
        ("Setup information", {
            'classes': ('mp_collapse mp_closed',),
            'fields': (
                'street',
                ('city', 'state'),
                ('country', 'postal_code'),
                ('phone', 'phone2'),
                )
            }),
        ]

#--------------------------------------------------------------------

class GroupAccountAdmin( AccountUsersFields, BaseTenantAdmin ):
    form = GroupAccountForm
    inlines = ( AccountInline, AccountInline2 )

    list_display = ( '__str__', 'user_count', 'admin_count', 'invite_code',
                     'beta_access', 'delivery_mode', 'notify_level',
                     'external_key', 'external_group' )
    list_editable = ( 'invite_code', 'delivery_mode', 'beta_access',
                      'external_key', 'external_group' )
    search_fields = ( 'base_account__name', 'notes',
                        # FUTURE - too expensive to include '=users__user__email', in search
                      'external_key', 'external_group', 'invite_code' )

    ordering = ('base_account__name',)

    filter_horizontal = ( 'users', 'admins' )

    fieldsets = [
        ("", {         # Name must match inline for staff level removal
            'classes': ('mp_placeholder base_account-group',),
            'fields' : (),
            }),
        ("", {
            # Added base account fields
            'classes': ('mp_collapse',),
            'fields': (
                'users',
                'invite_code',
                )
            }),
        (_("Account Admins"), {
            'classes': ('mp_collapse',),
            'fields': (
                'admins',
                'notify_level',
                )
            }),
        (_("Options"), {
            'mp_staff_level': 'access_high',
            'classes': ('mp_collapse mp_closed',),
            'fields': [
                'delivery_mode',
                ('beta_access','extended_access'),
                ('external_key','external_group'),
                ]
            }),
        (_("History"), {
            'mp_staff_level': 'access_all',
            'classes': ('mp_collapse mp_closed',),
            'fields': (
                ('hist_created','hist_modified'),
                )
            }),
        ("ROOT", {
            'mp_staff_level': 'access_root_menu',
            'classes': ('mp_collapse mp_closed',),
            'fields': (
                'sandbox',
                'options',
                )
            }),
        ]

    @property
    def can_ajax_save( self ):
        return False

    def save_related( self, request, form, formsets, change ):
        """
        Override save_related to save Account from account formset
        before saving M2M to handle case of new accounts.
        """
        for formset in formsets:
            for instance in formset.save( commit=False ):
                if not change and isinstance( instance, Account ):
                    # Create new account model when a new GA is created
                    ga = form.instance
                    account = instance
                    account.sandbox_id = ga.sandbox_id
                    account.group_account = ga
                    log.debug("New Account for GA: %s -> %s", ga, account)
                    account.save( check_health=False )
                instance.save()
        form.save_m2m()

    def get_queryset( self, request ):
        """
        Add aggregate counts to queryset for use in admin display
        """
        qs = super().get_queryset( request )
        qs = qs.annotate(
            user_count = Count( 'users', distinct=True ),
            admin_count = Count( 'admins', distinct=True ),
            )
        return qs

    def get_changelist_form( self, request, **kwargs ):
        # Ensure correct delivery mode
        return GroupAccountForm

    def user_count( self, obj ):
         return obj.user_count
    user_count.short_description = "Users"
    user_count.admin_order_field = 'user_count'

    def admin_count( self, obj ):
        return obj.admin_count
    admin_count.short_description = "Group admins"
    admin_count.admin_order_field = 'admin_count'

root_admin.register( GroupAccount, GroupAccountAdmin )


class GroupAccountStaffAdmin( StaffAdminMixin, GroupAccountAdmin ):
    pass

staff_admin.register( GroupAccount, GroupAccountStaffAdmin )
