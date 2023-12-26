#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    User proxy for the Account app, represents a customer
"""
from django.db.models import Q

from mpframework.common import log
from mpframework.foundation.tenant.models.base import TenantManager
from mpframework.user.mpuser.models import mpUser

from .account import Account


class AuManager( TenantManager ):

    def filter_account( self, account ):
        """
        Accounts may be tied through user relationships and
        through primary account relationships
        """
        if account:
            query = Q( primary_account=account ) | Q( ga_accounts__base_account=account )
            return self.mpusing('read_replica')\
                    .filter( query, sandbox=account.sandbox )

        return self.none()


    def merge_accounts( self, user, account ):
        """
        Support combining user accounts that were made by accident
        """
        assert user and account

        # Can pass in ids or objects
        if not isinstance( user, mpUser ):
            user = mpUser.Objects.get( id=user )
        if not isinstance( account, Account ):
            account = Account.objects.get( id=account )
        log.info("Merging user under one account: %s -> %s", user, account)

        # FUTURE -- will use similar code to GA add
