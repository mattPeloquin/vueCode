#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Optimize user and admin MTM fields:
        1) On initial load, only send users currently in account for
            use as both selected users and potential add users.
        2) To add users to account, use MTM horizontal_filter
"""
from django.contrib.admin.widgets import FilteredSelectMultiple

from mpframework.common.form import mpModelMultipleChoiceField

from ..models import AccountUser


# HACK - keep in sync with names of any Account user fields
USER_FIELDS = [ 'ga_users', 'admins', 'users' ]


class AccountUsersFields:
    """
    Mixin for admin classes dealing with assigning users to accounts
    """

    def formfield_for_manytomany( self, db_field, request, **kwargs ):
        """
        Override MTM horizontal_filter initialization to place all users
        associated with account into initial querylist.
        For the users -> group_account selection, the users are searched
        for dynamically. 
        """
        if db_field.name in USER_FIELDS:
            kwargs['form_class'] = AccountUsersField

            # For users that are part of an account is selected
            qs = AccountUser.objects.none()
            obj = request.mpstash.get('admin_obj')
            if obj:
                # HACK - Try relationship to account, and then base account
                account = getattr( obj, 'account',
                            getattr( obj, 'base_account', None ) )
                account = getattr( account, 'base_account', account )
                qs = AccountUser.objects.filter_account( account )

            # Use optimized transfer of userid and email
            kwargs['queryset'] = qs.values_list( 'id', 'user__email' )

        form_field = super().formfield_for_manytomany( db_field, request, **kwargs )

        # HACK - because Django sticks this help text in stupid place, have to override
        if db_field.name in USER_FIELDS:
            if isinstance( form_field.widget, FilteredSelectMultiple ):
                form_field.help_text = u"Select users and use arrows to move between groups"

        return form_field

class AccountUsersField( mpModelMultipleChoiceField ):
    """
    Override the users field to convert optimized lists of IDs
    into AccountUser objects for Django to save.
    """
    def result_queryset( self, value ):
        return AccountUser.objects.mpusing('read_replica')\
                .filter( id__in=value )
