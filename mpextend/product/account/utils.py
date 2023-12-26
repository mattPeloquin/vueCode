#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared code used inside and outside account app
"""
from django.conf import settings

from mpframework.common import log


def get_au( user ):
    """
    Safely provide AccountUser object if available
    Note this will cause a DB hit if account_user hasn't been select-related
    """
    if user and user.is_ready():
        au = getattr( user, 'account_user', None )
        staff = getattr( user, 'access_staff', None )
        if au:
            assert( not staff )
            return au
        if not staff:
            if user.is_authenticated:
                user.health_check()
                au = getattr( user, 'account_user', None )
                if au:
                    return au
                log.warning("ERROR DATA - Could not heal account_user: %s" % user)
            if settings.MP_TESTING and staff is None:
                raise Exception( "AnonymousUser in get_au: %s" % user )

def get_account( user ):
    au = get_au( user )
    if au:
        account = au.primary_account
        if account:
            return account
        else:
            msg = "ERROR DATA - User with no primary account: %s" % user
            if settings.MP_TESTING:
                raise Exception( msg )
            else:
                log.warning_quiet( msg )

def get_ga( user ):
    account = get_account( user )
    if account:
        return account.group_account
