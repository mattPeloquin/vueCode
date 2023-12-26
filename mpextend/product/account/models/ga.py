#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    GA (Group Account) extension of the account model

    FUTURE - Consider remove GA users MTM and change primary_account to account
"""
from django.conf import settings
from django.db import models
from django.db.models.signals import m2m_changed

from mpframework.common import log
from mpframework.common import constants as mc
from mpframework.common.model import CachedModelMixin
from mpframework.common.model.fields import YamlField
from mpframework.common.model.fields import mpImageField
from mpframework.common.cache import stash_method_rv
from mpframework.common.delivery import DELIVERY_MODES_ALL
from mpframework.foundation.tenant.models.base import SandboxModel

from ..utils import get_au
from .ga_manager import GroupAccountManager
from .au import AccountUser
from .apa import APA


class GroupAccount( CachedModelMixin, SandboxModel ):
    """
    Extends Account with additional support for multiple users sharing
    with reporting and admin by a user subset

    ALL Users associated with a GroupAccount are represented in
    the users MTM. In most cases those users will also have the Account
    for the GA set as their primary_account, but association with
    multiple GAs is supported.
    It is NOT valid to have a user who primary_account is set to
    the GA Account without being in users.
    """

    # All users this account is tied to, with the exception of the
    # nominal case of 1 and only 1 user attached via AccountUser primary account
    users = models.ManyToManyField( AccountUser, blank=True,
                related_name='ga_accounts', db_table='account_gauser',
                verbose_name=u"Users" )

    # Admin users for this account
    admins = models.ManyToManyField( AccountUser, blank=True,
                related_name='ga_admins', db_table='account_gauser_admin' )

    # Prefix for token for adding a new user to the account
    # If blank, the account invite URL is effectively turned off
    invite_code = models.CharField( max_length=mc.CHAR_LEN_UI_CODE, blank=True )

    # Optional image to identify the group
    image = mpImageField( blank=True, null=True )

    # Override default sandbox delivery settings
    delivery_mode = models.CharField( max_length=16, blank=True,
                choices=DELIVERY_MODES_ALL )

    # Notification level for emails sent to admin
    NOTIFY_LEVEL = (
        ( -1, u"No notifications" ),
        ( 0, u"Sign-ups" ),
        ( 10, u"Initial content access" ),
        ( 40, u"Badge completion" ),
        ( 50, u"Collection completion" ),
        ( 60, u"Item completion" ),
        ( 70, u"All content access" ),
        )
    notify_level = models.IntegerField( choices=NOTIFY_LEVEL, default=0 )

    # Can used for salesforce or other external integration
    external_key = models.CharField( max_length=mc.CHAR_LEN_UI_DEFAULT, blank=True,
                verbose_name=u"External ID" )
    external_group = models.CharField( max_length=mc.CHAR_LEN_UI_DEFAULT, blank=True,
                verbose_name=u"Custom groups" )

    # Give everyone on the group beta or extended access (overrides user setting)
    beta_access = models.BooleanField( default=False )
    extended_access = models.BooleanField( default=False )

    # Configurable override options
    options = YamlField( null=True, blank=True )

    # Notes entered by provider; this data participates in admin search
    notes = models.CharField( max_length=mc.CHAR_LEN_DB_SEARCH, blank=True )

    objects = GroupAccountManager()

    # GA is never accessed without underlying account
    select_related = ( 'base_account' ,)
    select_related_admin = select_related

    lookup_order = ('base_account__name',)

    class Meta:
        verbose_name = u"Group account"

    def __str__( self ):
        """
        Group account models get created in admin without initial
        account object, so need to handle that case
        """
        if self.dev_mode:
            return "ga({}s{}){}".format( self.pk, self.sandbox_id, self.name )
        return self.name

    @property
    def name( self ):
        account = getattr( self, 'base_account', None )
        return account.name if account else 'New group account'

    def invalidate( self ):
        """
        Clear account when we're invalidated (account may not be present
        during creation, so check it).
        """
        account = getattr( self, 'base_account', None )
        if account:
            account.invalidate()
        super().invalidate()

    def clone( self, **kwargs ):
        kwargs['name'] = self.name
        return super().clone( **kwargs )

    def has_user( self, user ):
        au = get_au( user )
        return au and self.users.filter( id=au.pk ).exists()

    def has_admin( self, user ):
        au = get_au( user )
        return au and self.admins.filter( id=au.pk ).exists()

    @property
    @stash_method_rv
    def image_url( self ):
        return self.image.url if self.image else ''

    def add_user( self, user ):
        """
        Add user to the account, optionally migrating user to group
        account by making primary and moving existing APAs
        """
        au = get_au( user )
        if not au:
            log.warning("GA user add without AU: %s -> %s", self, user)
            return
        return self.add_accountuser( au )

    def add_accountuser( self, au, migrate=None, all_apas=False ):
        """
        Add Account user from code
        """
        if not self.users.filter( id=au.pk ).exists():
            log.info2("GA ADD USER %s to %s", au.user, self)
            # Call _add_accountuser first to fixup framework, then add to the MTM table,
            # so the _add_accountuser code will be skipped in the MTM add signal
            self._add_accountuser( au, migrate, all_apas )
            self.users.add( au )
            return au

    def _add_accountuser( self, au, migrate=None, all_apas=False ):
        """
        Idempotent and potentially somewhat irreversible add au to GA,
        make the GA the AU's primary, and potentially migrate active or
        all existing APAs to the GA.

        Goal is to keep reasonably simple and handle the most likely business
        cases -- users attached to one account, either single or group.
        The organic creation of group accounts can be messy for
        customers, with individuals trying content and then transforming
        into a group account, so allow for that to occur, without
        worrying about all the edge cases of who bought what and
        what happens if user started single and left group account, etc.
        Those can be fixed up as backoffice activities.
        """
        log.debug2("GA add_user: %s <- %s, %s", self, au, au.primary_account)

        # Default is to migrate APAs from individual accounts
        if migrate is None:
            migrate = not au.primary_account.is_group
        if migrate:
            APA.objects.migrate_user_apas_to_account(
                            au, self.base_account, all_apas )

        if self.base_account != au.primary_account:
            log.info2("GA setting to primary: %s -> %s", au.user, self)
            au.primary_account = self.base_account
            au.save()

        au.user.invalidate()

    def remove_user( self, user ):
        """
        Remove user from the account
        """
        au = get_au( user )
        if au:
            self.users.remove( au )
            self.invalidate()


def _users_change( sender, **kwargs ):
    """
    Handle changes to GA users MTM relationship
    """
    if kwargs.get('reverse'):
        return

    # Migrate user to group account when added to group from single
    if kwargs.get('action') == 'post_add':
        ga = kwargs.get('instance')
        aus_added = kwargs.get('pk_set')
        log.debug("Users added to GA: %s -> %s", ga, aus_added)
        aus = AccountUser.objects.filter( id__in=aus_added )
        for au in aus.iterator():
            try:
                # FUTURE - when created in admin, this called before account created
                # from formset instance; need to change order to be able
                # to transfer users into a new GA
                if ga.base_account != au.primary_account:
                    log.debug("Adding user into group from MTM: %s", au)
                    ga._add_accountuser( au )

            except Exception as e:
                if settings.MP_DEV_EXCEPTION:
                    raise
                log.warning("GA Add error: %s, %s -> %s", ga, au, e)

    # Fixup AccountUser when users removed from GA
    if kwargs.get('action') == 'post_remove':
        ga = kwargs.get('instance')
        aus_removed = kwargs.get('pk_set')
        log.debug("Users removed from GA: %s -> %s", ga, aus_removed)
        aus = AccountUser.objects.filter( id__in=aus_removed )
        for au in aus.iterator():
            try:
                log.info2("GA user removed: %s -> %s", ga, au)
                if au.primary_account == ga.base_account:
                    log.debug("User primary reset after GA remove: %s", au)
                    au.primary_account = None
                    au.user.tracking.force_logout()

                au.health_check( save=True )

            except Exception as e:
                if settings.MP_DEV_EXCEPTION:
                    raise
                log.warning("GA Remove error: %s, %s -> %s", ga, au, e)

m2m_changed.connect( _users_change, sender=GroupAccount.users.through )
