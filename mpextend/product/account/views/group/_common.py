#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared view functionality for group accounts
"""

from mpframework.common import log
from mpextend.product.account.models import GroupAccount
from mpextend.product.account.utils import get_au

from ...group import mpGroupAccountException


def ga_admin_common( request, account ):
    """
    Returns context fixed up with common account admin data,
    including support for staff spoofing account admin screens
    """
    user = request.user
    accounts = []

    if user and user.access_staff:
        # Add list of accounts that could be switched to
        gas = GroupAccount.objects.mpusing('read_replica')\
                    .filter( sandbox=user.sandbox )
        for ga in gas.iterator():
            try:
                accounts.append( ga.base_account )
            except AttributeError:
                log.warning_quiet("ORPHAN GA account: %s", ga)
    else:
        # Get list of group accounts for the user
        au = get_au( user )
        if au:
            accounts = au.active_group_accounts

    accounts.sort( key=lambda a: a.name )

    if not account and accounts:
        account = accounts[0]
    if not account:
        raise mpGroupAccountException("No group accounts are available")

    context = {
            'ga_id': account.ga_id,
            'account': account,
            'accounts': accounts,
            }
    return account, context
