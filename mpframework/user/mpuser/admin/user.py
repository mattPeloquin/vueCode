#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Admin user screens
    Proxy models are used here to allow different admin user screens
"""

from copy import deepcopy

from mpframework.common.admin import root_admin
from mpframework.common.admin import staff_admin
from mpframework.common.admin import StaffAdminMixin
from mpframework.common.admin.large import AdminLargeMixin

from ..models import mpUser
from ..forms.password import SetPasswordForm
from .user_base import mpUserAdminBase
from .user_base import ReadyFilter


class mpUserStaffAdmin_All( StaffAdminMixin, AdminLargeMixin, mpUserAdminBase ):
    """
    Base functionality used across all staff user management screens
    Also provides view of users across sandboxes
    """
    list_display = ( '_sandbox', 'email', '_ready', 'email_verified', 'last_login',
                     'hist_created' )
    list_filter = ( '_sandbox', ReadyFilter, 'email_verified', 'is_active', 'last_login',
                    'hist_created', '_staff_level' )

    # Only superuser has privilege to set staff
    super_only_fieldsets = ( 'Staff' ,)

    # Override UserAdminBase name of admin change user password template
    # and change password form is special so make sure it gets parsley
    change_user_password_template = "admin/change_user_password.html"
    change_password_form = SetPasswordForm

    readonly_fields = mpUserAdminBase.readonly_fields + (
            'last_login', 'hist_created', 'email_changed', 'pwd_changed' )

    super_edit_fields = mpUserAdminBase.super_edit_fields + (
            'is_active', '_staff_level', 'is_superuser', 'staff_areas',
            'init_activation', 'init_terms' )

    def get_queryset( self, request ):
        """
        Ensure queryset provides view into users and staff only associated with
        the logged-in sandbox
        """
        qs = super().get_queryset( request )

        # Explicitly set sandbox to avoid provider users from seeing
        # users/staff from other sandboxes
        qs = qs.filter( sandbox=request.user.sandbox )

        # Ensure root users never show up in a provider's staff admin list
        # HACK - root provider ID is always 1
        qs = qs.exclude( _provider_id=1 )

        return qs

staff_admin.register( mpUser, mpUserStaffAdmin_All )


#--------------------------------------------------------------------
# Customer user management

class mpUserStaffAdmin_Customers( mpUserStaffAdmin_All ):
    """
    Add specific admin functionality for the sandbox user management view
    """
    list_display = ( 'email', 'first_name', 'last_name', '_primary_account', 'organization',
                     'title', '_delivery_mode', 'is_active', 'email_verified',
                     'last_login', 'hist_created' )
    list_filter = ( ReadyFilter, 'email_verified', 'last_login', 'hist_created' )

    list_editable = ( 'organization', 'title', '_delivery_mode', 'is_active' )

    def get_queryset( self, request ):
        return super().get_queryset( request ).filter(
                        _staff_level__isnull=True )

class mpCustomer( mpUser ):
    class Meta:
        proxy = True
        verbose_name = u"User"

staff_admin.register( mpCustomer, mpUserStaffAdmin_Customers )


#--------------------------------------------------------------------
# Staff user management

class mpUserStaffAdmin_Staff( mpUserStaffAdmin_All ):
    """
    Add specific admin functionality for the provider staff management view
    """
    list_display = ( 'email', '_staff_level', '_superuser', 'workflow_level', 'last_login' )
    list_filter = ( '_staff_level' ,)

    def get_queryset( self, request ):
        return super().get_queryset( request ).filter(
                        _staff_level__isnull=False )

    def get_list_display( self, request ):
        user = request.user
        rv = super().get_list_display( request )

        # Add staff-level items to display
        rv = list( rv )
        if user.access_med:
            rv.insert( 2, 'staff_areas' )
            rv.insert( 5, '_all_sandboxes' )
        if user.is_owner:
            rv.insert( 6, '_owner' )

        return rv

    def get_list_editable( self, request ):
        user = request.user
        rv = super().get_list_editable( request )
        if user.is_superuser:
            rv += ( 'staff_areas', '_staff_level', 'workflow_level' )
        return rv

class mpStaff( mpUser ):
    class Meta:
        proxy = True
        verbose_name = u"Staff user"

staff_admin.register( mpStaff, mpUserStaffAdmin_Staff )

#--------------------------------------------------------------------

class mpUserRootAdmin( AdminLargeMixin, mpUserAdminBase ):
    """
    This is only seen in the root admin
    """
    list_display = ( '_provider', '_sandbox', 'email',
                     '_staff', '_staff_level', 'sandboxes_level', '_superuser', '_is_owner',
                     'workflow_level', '_has_test_access', '_ready', 'is_active',
                     'last_login', 'hist_created' )
    list_filter = ( '_provider', '_staff_level', 'is_superuser', '_is_owner',
                    ReadyFilter, 'last_login', 'hist_created', )

    search_fields = ( 'email', '_provider__name', '_provider__system_name',
                        '_sandbox__name', '_sandbox__subdomain' )

root_admin.register( mpUser, mpUserRootAdmin )
