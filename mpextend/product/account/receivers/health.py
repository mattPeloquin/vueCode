#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Account syncing for healthchecks
"""
from django.dispatch import receiver

from mpframework.common import log
from mpframework.user.mpuser.signals import mpuser_health_check
from mpframework.content.mpcontent.access import has_free_access

from ..models import AccountUser


@receiver( mpuser_health_check )
def handle_mpuser_health_check( **kwargs ):
    """
    Make sure there is a valid account attached to a user, or
    make sure staff accounts do not have one.
    """
    user = kwargs.get('user')

    if user.access_staff:
        if hasattr( user, 'account_user' ):
            try:
                log.info("HEAL - removing staff account_user: %s", user)
                user.account_user.delete()
            except Exception:
                log.exception("Problem removing staff account user: %s", user)
        return

    # Don't create account if sandbox allows free access to everything
    if has_free_access( user ):
        return

    # If a group account requested, try to assign user to it
    account = None
    info = kwargs.get( 'create_info', {} )
    ga = info and info.get('group_account')
    if ga:
        account = ga.base_account
        if not account:
            log.warning("ERROR DATA - GA user create invalid: %s -> %s", user, ga)

    # Add account user if not present
    if not hasattr( user, 'account_user' ):
        log.info("HEAL - Creating new AcccountUser for: %s", user)
        au = AccountUser( sandbox=user.sandbox, user=user, primary_account=account )
        au.save()

    user.account_user.health_check()
