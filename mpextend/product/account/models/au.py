#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    User proxy for the Account app, represents a customer
"""
from django.db import models

from mpframework.common import log
from mpframework.common.model import CachedModelMixin
from mpframework.common.cache import stash_method_rv
from mpframework.common.logging.timing import mpTiming
from mpframework.foundation.tenant.models.base import SandboxModel
from mpframework.user.mpuser.models import mpUser
from mpextend.product.catalog.models import PA

from .account import Account
from .au_manager import AuManager


class AccountUser( CachedModelMixin, SandboxModel ):
    """
    Non-staff users have a 1:1 AccountUser proxy to track their
    attachment to an account and APAs.
    """
    user = models.OneToOneField( mpUser, models.CASCADE,
                related_name='account_user' )

    """
    Users may be attached to multiple accounts, but one account
    is considered primary at all times, with licenses applied first.
    Empty primary account is allowed for various transition cases where
    the account is being changed and will be filled in via healing
    Don't delete account with user, because group accounts share
    """
    primary_account = models.ForeignKey( Account, models.SET_NULL,
                blank=True, null=True, related_name='primary_aus' )

    objects = AuManager()

    select_related = ( 'user' ,)
    select_related_admin = select_related + ( 'primary_account' ,)

    lookup_fields = ( 'user__email__icontains', 'user__first_name__icontains',
                'user__last_name__icontains' )
    lookup_order = ('primary_account__name',)

    def __str__( self ):
        if self.dev_mode:
            return "au({}-{})".format( self.pk, self.user )
        return str( self.user )

    def save( self, *args, **kwargs ):
        # Force initial save if not created yet for MTM relationship
        if not self.pk:
            super().save( *args, **kwargs )
        # Normally check health, then save
        self.health_check( save=False )
        super().save( *args, **kwargs )

    def invalidate( self ):
        """
        AccountUser only directly stashes vs. caches information,
        and is invalidated when user is invalidated, so don't
        trigger other invalidation.
        """
        self.clear_stash()
        if self.primary_account:
            self.primary_account.invalidate()

    """--------------------------------------------------------------------
        Normally a user will be in a single individual or group account, or
        may have migrated from individual to group.
        A maximum of one individual user account is all that makes sense,
        while multiple group account support is provided to allow a single user
        to share access across groups.
    """
    def health_check( self, save=True ):
        """
        Ensure health of account user relationships
        Handle cases such as user added/removed from group account
        """
        dirty = False
        user = self.user
        log.debug2("AccountUser health check: %s", user)
        assert not user.is_staff
        self.invalidate()

        if not self.primary_account:
            # Try to set to an active account
            if self.active_accounts:
                account = self.active_accounts[0]
                log.info("HEAL - Setting ua primary to: %s -> %s", user, account)
            # Or set to single-user account, either existing or new
            else:
                existing = Account.objects.filter( sandbox=self.sandbox, name=self.user.email )
                if existing:
                    account = existing.first()
                    log.info("HEAL - Setting ua primary to single: %s -> %s", user, account)
                else:
                    log.info("HEAL - User with no accounts, making new single: %s", user)
                    account = Account( sandbox=self.sandbox, name=self.user.email )
                    account.save( check_health=False )

            self.primary_account = account
            dirty = True

        # Healthy accounts have primary that is in active account list
        # If no active primary account, try to set account to first active
        if self.active_accounts:
            if self.primary_account and self.primary_account in self.active_accounts:
                log.detail3("User has active account: %s -> %s", user, self.primary_account)
            else:
                new_primary = self.active_accounts[0]
                log.info("HEAL - setting primary account: %s -> %s", user, new_primary)
                self.primary_account = new_primary
                dirty = True
        # If primary is a group account, make sure user in GA user list
        ga = self.primary_account.group_account
        if ga and not ga.users.filter( id=self.pk ).exists():
            log.info("HEAL - User GA primary, not in users: %s -> %s", user, ga)
            ga.add_accountuser( self )

        if save and dirty:
            self.save()
        return dirty

    @property
    @stash_method_rv
    def accounts( self ):
        """
        Return all accounts that can actively participate in granting a license.
        Places primary first for loop checks, looks for a single user account if
        in a group account, and adds any other group accounts.
        """
        rv = []
        if self.primary_account:
            rv = [ self.primary_account ]
            if self.primary_account.is_group:
                # Check for individual account; don't freak out if more than one
                individual = Account.objects.filter( sandbox=self.sandbox,
                                                     name=self.user.email )
                if individual:
                    rv.extend([ individual.first() ])
        # Add any additional group accounts
        rv.extend([ ga for ga in self.ga_account_list if
                        ga.pk != self.primary_account_id ])
        return rv

    @property
    @stash_method_rv
    def ga_account_list( self ):
        return [ ga.base_account for ga in self.ga_accounts.all() if ga.base_account ]

    @property
    @stash_method_rv
    def active_accounts( self ):
        if not self.user.is_active:
            return []
        return [ a for a in self.accounts if a.is_active ]

    @property
    @stash_method_rv
    def active_group_accounts( self ):
        return [ a for a in self.active_accounts if a.is_group ]

    @property
    @stash_method_rv
    def active_admin_accounts( self ):
        return [ a for a in self.active_group_accounts if a.has_admin( self.user ) ]

    @stash_method_rv
    def is_group_admin( self, account=None ):
        """
        If account provided, return true only if admin for that group account
        If no account provided, return number of active accounts they are admin for
        """
        log.debug2("Checking account admin: %s -> %s", self, account)
        if self.user.access_staff:
            return self.user.sees_group
        elif account:
            return bool( account in self.active_admin_accounts )
        else:
            return len( self.active_admin_accounts )

    @property
    @stash_method_rv
    def beta_access( self ):
        return any( a.group_account.beta_access for a in self.active_group_accounts )

    @property
    @stash_method_rv
    def extended_access( self ):
        return any( a.group_account.extended_access for a in self.active_group_accounts )

    @property
    @stash_method_rv
    def delivery_mode( self ):
        """
        Does the user's primary account have delivery mode set to compatibility?
        Sandbox and user mode should be checked through the user object.
        """
        if self.primary_account and self.primary_account.is_group:
            return self.primary_account.group_account.delivery_mode

    @property
    @stash_method_rv
    def options( self ):
        """
        If use belongs to a group account with options, return them
        """
        if self.primary_account and self.primary_account.is_group:
            return self.primary_account.group_account.options

    #--------------------------------------------------------------------
    # User content access through catalog configuration

    @stash_method_rv
    def active_apas( self, content_tags=None ):
        """
        Return list of active APAs this user is connected to, with optional tag matching.
        KEY CONTENT ACCESS POINT; all content requests use this for APA list.
        Leverages the my_apas list to limit need to hit DB.
        """
        log.detail3("Checking au active_apas: %s, tags(%s)", self.user, content_tags)
        rv = set()
        for apa in self.my_apas:
            log.detail3("Considering apa: %s", apa)
            if apa.is_active( save=True, deep=False ):
                if not content_tags or any(
                        apa.matches_tag( tag ) for tag in content_tags ):
                    log.detail3("  adding apa")
                    rv.add( apa )
        log.debug2("ACTIVE APAs: %s, %s -> %s", self.user, content_tags, rv)
        return list( rv )

    @property
    @stash_method_rv
    def my_apas( self ):
        """
        Return list of ALL APAs this for active accounts the user is connected to
        """
        rv = set()

        # There are edge cases where a user's accounts get out of whack
        # but they are not healed via login because of an active session
        # Heal here to ensure access to free content
        if not self.active_accounts and not self.user.access_staff:
            log.warning("HEAL - User had no accounts in APA request: %s", self)
            self.health_check()

        # Get all APAs for user accounts that they are related to
        for account in self.active_accounts:
            for apa in account.get_apas( user=self.user ):
                 rv.add( apa )

        log.debug("USER APAs: %s -> %s", self.user, rv)
        return list( rv )

    @property
    @stash_method_rv
    def my_pas( self ):
        """
        Return dict of PAs associated with this user based on active and
        inactive APAs. Keyed by PA id, and each PA enriched with reference to
        the APAs tied to this user.
        """
        pas = {}
        for apa in self.my_apas:
            pa = apa.pa
            if not pa.pk in pas:
                pa.__my_apas = []
                pas[ pa.pk ] = pa
            (pas[ pa.pk ]).__my_apas.append( apa )
        log.debug2("ALL PAs: %s -> %s", self.user, pas)
        return pas

    @stash_method_rv
    def active_pas( self, content_tags=None ):
        """
        Return list of active PAs associated with this user
        """
        log.detail3("Checking active pas: %s, tags(%s)", self.user, content_tags)
        rv = set()
        for apa in self.active_apas( content_tags ):
            rv.add( apa.pa )
        log.debug2("ACTIVE PAs: %s, %s -> %s", self.user, content_tags, rv)
        return list( rv )

    def pa_is_visible( self, pa ):
        """
        Can this user current see the PA?
        """
        if pa.visible_to_all:
            return True
        for account in self.active_accounts:
            if pa.visible_to_account( account ):
                return True

    @property
    @stash_method_rv
    def available_pas( self ):
        """
        Return list of potential PAs for the user, which is:
          - Public PAs that are active
          - PAs specific to any of the user's accounts
              MINUS
          - PAs that have already been used up
          - PAs with active APA on a users's account
        """
        if log.debug_on():
            log.debug("START AVAILABLE PAS: %s", self.user)
            t = mpTiming()
        rv = set()
        pas = list( PA.objects.get_available_pas( self.user.sandbox.pk ) )

        # Go through the PAs to determine ones to offer
        log.debug("Checking PAs for user access: %s -> %s", self.user, len(pas))
        for pa in pas:
            log.detail3("---- Considering PA: %s ----", pa)

            if not self.pa_is_visible( pa ):
                continue

            if pa.pk in self.my_pas:
                # If PA is/was owned, check if still available
                my_pa = self.my_pas[ pa.pk ]
                available_apas = [ apa.has_more_uses and not apa in self.active_apas()
                            for apa in my_pa.__my_apas ]
                if all( available_apas ):
                    log.debug2("  adding existing PA: %s", pa)
                    rv.add( pa )
            else:
                log.debug2("   adding PA: %s", pa)
                rv.add( pa )

        if log.debug_on():
            log.debug("END AVAILABLE PAs (%s): %s -> %s, %s", t,
                    self.user, len(pas), len(rv))
        return list( rv )

