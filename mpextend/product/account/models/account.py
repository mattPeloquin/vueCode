#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Accounts bring together account details, billing info,
    and PA history for one or a group of users.

    Provides key connection between users and PAs, via the APA.

    FUTURE - Consider remove GA users MTM and change primary_account to account
"""
from django.db import models
from django.conf import settings

from mpframework.common import log
from mpframework.common import constants as mc
from mpframework.common.model import CachedModelMixin
from mpframework.common.model.contact_mixin import ContactMixin
from mpframework.common.cache import stash_method_rv
from mpframework.foundation.tenant.models.base import SandboxModel
from mpframework.foundation.tenant.models.base import TenantManager
from mpextend.product.catalog.models import PA

from .apa import APA


class AccountManager( TenantManager ):

    def lookup_queryset( self, sandbox ):
        qs = super().lookup_queryset( sandbox )
        qs = qs.filter( status='A' )
        return qs


class Account( ContactMixin, CachedModelMixin, SandboxModel ):
    """
    Non-staff users are associated with ONE Account at all times,
    but that account may change over time.
    Users sharing an account share PAs and billing.

    This model along with GroupAccount and AccountUser supports three
    types of account-user relationships:

        - Individual. Nominal account for a retail customer,
        representing a single person using content in a sandbox.

        - Group. Groups of users representing an organization
        that purchases content from the sandbox. Supports customer
        admins and reporting.

        - Shared. Multiple AccountUsers primary_accounts point at
        the same account, with no GroupAccount.
        FUTURE - not currently used, could support small group purchases

    FULL ENTERPRISE ACCOUNT MANAGEMENT ISN'T PLANNED, would require
    hierarchical structure, robust roles, etc. That requires modeling many
    permutations corporations might demand. The current structure can
    support group accounts of 1000s, with really large accounts being split
    up by group or department.

    Accounts have few assumptions about customer/company structure, to support
    arbitrary scenarios of team managers, groups, etc.
    For example, if 5 different teams or individuals in the same company
    sign themselves up they'll each just create their own Account.
    If later the company converts to a GroupAccount, it will be a back-office
    admin task to create a new GA and APA representing the contracts,
    move or invite users onto that contract, pro-rate billing, etc.
    """

    # Name tied to the account
    # For individual accounts this is populated with user email to facilitate
    # reporting and searching.
    # For group and shared accounts it can be updated
    name = models.CharField( db_index=True, max_length=mc.CHAR_LEN_UI_DEFAULT )

    # Define APA licenses as the through table for all
    # product agreements this account has executed/purchased
    pas = models.ManyToManyField( PA, through=APA,
                related_name='accounts', blank=True )

    # Group account meta data is an extension of an account
    group_account = models.OneToOneField( 'account.GroupAccount', models.CASCADE,
                related_name='base_account', blank=True, null=True )

    # Accounts are kept in system for history, but state can change
    STATUS = (
        ('A', u"Active"),       # Participating as an active user account
        ('R', u"Retired"),      # Account cannot make new purchases
        ('S', u"Suspended"),    # Account cannot use any licenses
        )
    status = models.CharField( max_length=1, choices=STATUS, default='A' )

    # Comma-delimited set of arbitrary text codes associated with account
    # Used in reporting and targeting PAs and Coupons to specific accounts
    codes = models.CharField( max_length=mc.CHAR_LEN_UI_LINE, blank=True )

    objects = AccountManager()

    select_related_admin = ('group_account',)

    lookup_fields = ('id__iexact', 'name__icontains',
                 'group_account__users__user__email__icontains')
    lookup_order = ('-group_account', 'name')

    class Meta:
        verbose_name = u"Account"

    def __str__( self ):
        if self.dev_mode:
            return "a({}s{}){}".format( self.pk, self.sandbox_id, self.name )
        else:
            return self.name

    def save( self, *args, **kwargs ):
        if( kwargs.pop( 'check_health', True ) ):
            self.health_check( save=False )
        super().save( *args, **kwargs )

    def health_check( self, save=True ):
        """
        Log errors for bad state, and heal what is possible
        """
        dirty = False
        try:
            au = self.primary_aus.first()
            if au:
                if not self.name:
                    new_name = au.user.email
                    log.info("HEAL account name: %s -> %s", self.pk, new_name)
                    self.name = new_name
                    dirty = True
            elif not self.is_group:
                log.warning("Orphan Account with no users: %s", self.pk)

            if save and dirty:
                self.save()
        except Exception as e:
            if settings.MP_DEV_EXCEPTION:
                raise
            log.warning("Account exception, no group or primary user: %s -> %s", self.pk, e)

    @property
    def dict( self ):
        return {
            'id': self.pk,
            'name': self.name,
            'postal_code': self.postal_code,
            'country': self.country,
            }

    #--------------------------------------------------------------------

    @property
    def is_single( self ):
        return not self.is_group and not self.is_shared

    @property
    @stash_method_rv
    def is_shared( self ):
        return not self.is_group and self.primary_aus.count() > 1

    @property
    def is_group( self ):
        return bool( self.group_account )

    @property
    def is_active( self ):
        return self.status in ['A']

    @property
    def ga_id( self ):
        return self.group_account_id if self.is_group else '_'

    @property
    @stash_method_rv
    def user_ids( self ):
        """
        Returns list of user ids for users attached to account
        """
        if self.group_account:
            return list( self.group_account.users.mpusing('read_replica')\
                            .values_list( 'user_id', flat=True ) )
        else:
            return self.primary_user_ids

    @property
    @stash_method_rv
    def primary_user_ids( self ):
        return list( self.primary_aus.mpusing('read_replica')\
                        .values_list( 'user_id', flat=True ) )

    def has_admin( self, user ):
        if self.group_account:
            return self.group_account.has_admin( user )

    def has_owner( self, user ):
        return self.has_admin( user ) or user.pk in self.primary_user_ids

    """--------------------------------------------------------------------
        APA support
    """

    def get_tax( self ):
        """
        Returns information for tax based on this account's postal code
        and tax information encoded in the sandbox tax YAML field.
        Returns None if no tax is configured.
        FUTURE for now just a percent lookup based on postal code, but more
        elaborate logic could be added.
        """
        tax_name = None
        percent = 0
        try:
            taxes = self.sandbox.taxes

            # Check for global tax case
            if taxes['global']:
                tax_name = u"Purchase"
                percent = taxes['global.percent']

            # Handle postal code ranges
            elif self.postal_code:
                for name, tax in taxes['postal_codes'].items():
                    if( self.postal_code >= tax['lower'] and
                            self.postal_code <= tax['upper'] ):
                        tax_name = name
                        percent = tax['percent']
                        break

            log.info2("Adding tax: %s, postal: %s -> %s, %s",
                         self, self.postal_code, tax_name, percent)
        except Exception as e:
            log.info("CONFIG - TAX error: %s -> %s -> %s",
                        self, self.postal_code, e)
        if tax_name:
            return {
                'name': tax_name,
                'percent': float( percent ),
                'inclusive': False,
                }

    def get_apas( self, **kwargs ):
        """
        Returns all apas associated with account
        Can use kwargs to filter active or not, user, and product
        """
        return APA.objects.get_apas( self, **kwargs )

    def get_apas_dict( self, **kwargs ):
        """
        Returns activated APAs in dict to support easy json conversion
        """
        rv = []
        for apa in self.get_apas( **kwargs ):
            log.detail3("Adding apa to account apa dict: %s", apa)
            try:
                rv.append( apa.dict )
            except Exception as e:
                log.warning_quiet("Error creating account apa row: %s => %s => %s", self, apa, e)
        return rv
