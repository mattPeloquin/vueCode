#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Group account manager
"""
from django.db import transaction

from mpframework.common import log
from mpframework.common.utils import now
from mpframework.foundation.tenant.models.base import TenantManager


class GroupAccountManager( TenantManager ):

    @transaction.atomic
    def create_obj( self, **kwargs ):
        from .account import Account
        sandbox = kwargs.pop('sandbox')
        name = kwargs.pop('name')
        kwargs['invite_code'] = kwargs.pop( 'invite_code', '{}{}'.format( name, now().year ) )
        log.info("Creating group account: %s -> %s", sandbox, name )

        ga = self.model( sandbox=sandbox, **kwargs )
        ga.save()
        account = Account( sandbox=sandbox, group_account=ga, name=name )
        account.save()

        log.debug("Created new GroupAcccount: %s -> %s", sandbox, ga)
        return ga

    def hard_migrate_all_users( self, ga ):
        """
        Idempotent and somewhat irreversible full migration of every user
        attached to the group account fully into the group account.
        Differences between this and normal migrate:
         - Inactive APAs will be transferred
         - Delete user's individual account if it exists
        """
        if not isinstance( ga, self.model ): ga = self.get( id=ga )
        log.info("Hard migrate of GA users: %s", ga)
        for au in ga.users.all().iterator():
            old_active = au.primary_account
            ga.add_accountuser( au, all_apas=True )
            if old_active and not old_active.is_group:
                log.info("REMOVING old individual account: %s -> %s", au, old_active)
            old_active.delete()
