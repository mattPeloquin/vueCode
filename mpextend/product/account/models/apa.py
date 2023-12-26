#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    License / APA (AccountProductAgreement)

    APA/License: MTM THROUGH TABLE between Accounts and PAs
     - APA record represents a license for a purchase, trial, or other access
     - Defines which Account the APA applies to
     - Links the Account to 1 or more instances of a PA
     - Tracks and manages the license
"""
from decimal import Decimal
from django.db import models
from django.db.models import Q

from mpframework.common import log
from mpframework.common import constants as mc
from mpframework.common.cache import stash_method_rv
from mpframework.common.model import CachedModelMixin
from mpframework.common.model.fields import YamlField
from mpframework.common.model.fields import mpDateTimeField
from mpframework.common.utils import tz
from mpframework.common.utils import now
from mpframework.common.utils import safe_int
from mpframework.common.utils import timestamp
from mpframework.foundation.tenant.models.base import SandboxModel
from mpframework.content.mpcontent.tags import ContentTagMatchMixin
from mpextend.product.catalog.models import PA
from mpextend.product.catalog.access_period import AccessPeriodMixin
from mpextend.product.catalog.access_pricing import AccessPricingMixin

from ..signals import apa_update
from ..signals import apa_add_users
from ..utils import get_au
from .apa_manager import ApaManager


class APA( ContentTagMatchMixin, AccessPeriodMixin, AccessPricingMixin,
            CachedModelMixin, SandboxModel ):
    """
    APAs/Licenses grant users access to content.

    Access is controlled by the EXISTENCE of an ACTIVE APA:
      - Tied to a user through an account
      - Tied to content through license tag matches
    ACTIVE means the APA is activated, its END DATE HASN'T EXPIRED,
    and it has room in points/seconds/users if metering is on.

    APAs can represent free trials, purchases, and subscriptions.
    APAs are created both programmatically and manually (backoffice).
    They are normally not deleted, providing history of transactions,
    and are reused for subscriptions, updates, one-use-trials, etc.

    APAs support renewal through automated subscriptions or manual user action.
    An APA is renewed by extending the end date by the current access period.

    APA behavior varies based on the Agreement, PA, and Coupon used
    to create it; see PA and Agreement rules comments for how this works.
    Once created, aspects of the APA can be modified, but its fundamental
    type should not (normally) be changed (e.g., avoid reusing an APA to
    convert a one-time purchase to subscription).

    Single-user APAs have two possible paths:
      - APA for a non-group Account that is primary for an AccountUser
      - APA for GA with 1 selected user in ga_users

    Multi-user APA has two possible paths:
      - GA "group/site license" that applies to all users in GA
      - APA for GA where user is in ga_users MTM

    Automated payments are managed by the payment apps; the APA only tracks
    state and usuage history for the current access period.

    FUTURE - support APA without a PA?
    """
    account = models.ForeignKey( 'account.Account', models.CASCADE,
                related_name='apas' )
    pa = models.ForeignKey( PA, models.CASCADE, related_name='apas',
                verbose_name=u"Pricing option" )

    # Date after which the APA becomes inactive
    # Used for one-time usage, single payments, and subscriptions
    # If blank, the APA is perpetual (usually for backoffice licenses)
    period_end = mpDateTimeField( db_index=True, blank=True, null=True )

    # Track active state in DB for admin ease/optimization and to allow disabling
    # Automation may set this to off (e.g., when expired), but never sets
    # to on after a manual off
    _is_active = models.BooleanField( default=True, db_column='is_active',
                verbose_name=u"Active" )

    # Flag allowing creation of inactive APA records early during purchase.
    # Inactive APA records may be culled.
    is_activated = models.BooleanField( default=False )

    # The number of SKU units this APA applies to
    sku_units = models.IntegerField( blank=True, null=True )

    # Overrides and additions to Agreement rules
    # HACK SCALE DB MIGRATE - manually add a FULLTEXT index for DB WHERE clauses
    _rules = YamlField( null=True, blank=True, db_column='rules' )

    # Start of the current access period
    period_start = mpDateTimeField( db_index=True, blank=True, null=True )

    # Access period tracking, notes, and long-term history stored in YAML
    # Participates in admin search
    # HACK SCALE DB MIGRATE - manually add a FULLTEXT index for DB search
    data = YamlField( null=True, blank=True )

    # Type of purchase transaction the APA represents
    PURCHASE_TYPE = (
        ('F', u"Online free"),
        ('P', u"Online purchase"),
        ('C', u"Online coupon"),
        ('B', u"Backoffice"),
        )
    PURCHASE_TYPE_LOOKUP = dict( PURCHASE_TYPE )
    purchase_type = models.CharField( max_length=1,
                choices=PURCHASE_TYPE, default='B' )

    # Coupon CODE used to create license; part of defining a unique
    # license creation since it can modify attributes
    coupon = models.CharField( db_index=True, blank=True,
                max_length=mc.CHAR_LEN_UI_CODE )

    # Optional custom name, for staff partition/reporting in group accounts
    # or potentially for value shown in payments
    custom_name = models.CharField( db_index=True, blank=True,
                max_length=mc.CHAR_LEN_UI_LINE )

    """----------------------------------------------------------
        Fields only used with Group Accounts (GAs)
        These are NOT USED with APAs for single-user accounts

        ga_license determines if APA is a group license for a GA.
        If so, all users attached to account can use APA,
        if not ga_users is subset of GA users that can use this APA,
        and ga_users_max is an optional limit.
    """
    ga_license = models.BooleanField( default=True )
    ga_users = models.ManyToManyField( 'account.AccountUser', blank=True,
                related_name='ga_apas', db_table='account_gauser_apa',
                verbose_name=u"Users" )
    ga_users_max = models.IntegerField( blank=True, null=True )

    class Meta:
        verbose_name = u"License"

    objects = ApaManager()

    select_related = ( 'account', 'pa', 'pa__agreement' )
    select_related_admin = select_related + (
                'account__group_account', )

    lookup_fields = ( 'id__iexact', 'custom_name__icontains',
                'pa__sku__icontains', 'pa___name__icontains' )

    # Fields that are controlled by PA when control_apas is set
    pa_control_fields = ( '_is_active', '_tag_matches', 'access_end', '_rules' )

    def __str__( self ):
        if self.dev_mode:
           return "{}({})".format( self.name, self.pk )
        return self.name

    def _log_instance( self, message ):
        log.debug_on() and log.detail3("%s APA: %s -> %s, %s (%s)", message,
                                 self.pk, self.account_id, self.pa_id, id(self))

    def clone( self, **kwargs ):
        raise Exception("APAs should never be cloned")

    @property
    def dict( self ):
        return {
            'id': self.pk,
            'active': self.is_active( save=True ),
            'name': self.name,
            'price': self.access_price,
            'subscription': self.is_subscription,
            'trial': self.is_trial,
            'coupon': self.coupon,
            'purchase_type': self.purchase_type_lookup,
            'units': self.units,
            'description': self.description,
            'period_start': self.period_start_date,
            'period_end': self.period_end_date,
            'user_count': self.user_count,
            'user_info': self.user_info,
            'default_mode': self.default_mode,
            }

    @property
    def default_name( self ):
        return "{} - {}".format( self.pa.sku, self.account.name )

    @property
    def name( self ):
        return self.custom_name if self.custom_name else self.default_name

    def add_history( self, info, user=None, save=True ):
        if user and user.access_root:
            return
        user = " {}".format( user.email ) if user else ""
        new_text = "{}{} - {}\n".format( timestamp(), user, info )
        new_text = new_text + self.data.get( 'history', "" )
        self.data.set( 'history', new_text )
        if save:
            self.save()

    #--------------------------------------------------------------------
    # License management

    @property
    def access_period( self ):
        return self._access_period or self.pa.access_period

    @property
    @stash_method_rv
    def tag_matches( self ):
        return self._tag_matches or self.pa.tag_matches

    @property
    def unit_price( self ):
        return self.pa.unit_price if self._unit_price is None else self._unit_price
    @property
    def paygo_price( self ):
        return self.pa.paygo_price if self._paygo_price is None else self._paygo_price

    @staticmethod
    def is_free_Q():
        """
        This is only for admin display, so won't capture all permutations,
        but get the most likely ones.
        """
        return (
            Q( _rules__icontains='access_free: true' ) |
            Q( pa___rules__icontains='access_free: true' ) |
            (  ( Q( _unit_price__lte=0 ) | ( Q(_unit_price__isnull=True) & (
                     Q(pa___unit_price__lte=0) | Q(pa___unit_price__isnull=True) ) )
                ) &
               ( Q( _paygo_price__lte=0 ) | ( Q(_paygo_price__isnull=True) & (
                     Q(pa___paygo_price__lte=0) | Q(pa___paygo_price__isnull=True) ) )
                ) &
              ~Q( Q( _rules__icontains='initial_price' ) |
                  Q( pa___rules__icontains='initial_price' )
                 )
             ) )

    @staticmethod
    def is_subscription_Q():
        return (
            Q( _rules__icontains='auto_renew: true' ) |
            Q( pa___rules__icontains='auto_renew: true' )
            )

    @staticmethod
    def is_reusable_Q():
        return (
            ~Q( _rules__icontains='one_time_use: true' ) &
            ~Q( pa___rules__icontains='one_time_use: true' )
            )

    @property
    def units( self ):
        return self.sku_units if self.sku_units else 1

    @property
    def description( self ):
        rv = self.pa.description
        if self.units > 1:
            rv += u" ({} units)".format( self.units )
        return rv

    @property
    def paygo_units( self ):
        """
        For any metering, figure out any paygo usage overage, and
        provide the largest one.
        """
        points = self.base_points and self.paygo_points
        if points:
            points = abs( self.base_points - self.rules.get( 'usage_points', 0 ) )
            points = points // self.paygo_points
        users = self.base_users and self.paygo_users
        if users:
            users = abs( self.base_users - self.rules.get( 'usage_users', 0 ) )
            users = users // self.paygo_users
        minutes = self.base_minutes and self.paygo_minutes
        if minutes:
            minutes = abs( self.base_minutes -
                            ( self.rules.get( 'usage_seconds', 0 ) // 60 ) )
            minutes = minutes // self.paygo_minutes
        log.debug2("APA paygo units: %s -> p:%s u:%s t:%s", self,
                points, users, minutes)
        return max( points, users, minutes )

    # These return 0 if metering not set, or value based on current units
    @property
    def base_points( self ):
        return self.units * self.rules.get( 'unit_points', 0 )
    @property
    def base_users( self ):
        return self.units * self.rules.get( 'unit_users', 0 )
    @property
    def base_minutes( self ):
        return self.units * self.rules.get( 'unit_minutes', 0 )

    # These return 0 if hard cap is set, or usage increment
    @property
    def paygo_points( self ):
        return self.rules.get( 'paygo_points', 0 )
    @property
    def paygo_users( self ):
        return self.rules.get( 'paygo_users', 0 )
    @property
    def paygo_minutes( self ):
        return self.rules.get( 'paygo_minutes', 0 )

    def get_period_end( self, period_start=None ):
        """
        Calclate a next period end date from the given start date.
        Returns none if perpetual.
        """
        period_start = period_start or self.period_start
        period = self.access_period_delta
        if period:
            period_end = period_start + period
            if not self.access_end or period_end < self.access_end:
                return period_end
        if self.access_end:
            return self.access_end

    @property
    def expire( self ):
        return self.access_end

    @property
    def renewals( self ):
        return self.data.get( 'renewals', 0 )

    @property
    def period_end_date( self ):
        return tz( self.period_end ).date() if self.period_end else ''
    @property
    def period_start_date( self ):
        return tz( self.period_start ).date() if self.period_start else ''
    @property
    def expire_date( self ):
        return tz( self.expire ).date() if self.expire else ''

    @property
    @stash_method_rv
    def rules( self ):
        """
        Combine agreement and PA rules
        """
        rv = self.pa.rules
        rv.update( self._rules )
        return rv

    def save( self, *args, **kwargs ):
        """
        APAs may be saved 2-3 times during initial creation, due to need to setup
        MTM relationships and keep code simple around activation
        """
        user = kwargs.pop( '_user', None )
        admin = kwargs.pop( '_admin', False )
        activate = kwargs.pop( '_activate', None )

        # Is this the creation of the record? (or a forced reset)
        if not self.pk or kwargs.pop( '_force_init', False ):
            self._create_init( user, admin )
            # Activate new record immediately if backoffice
            if not activate and admin:
                activate = u"BACKOFFICE create"

        # Activate if active flag was set and not activated yet (admin override)
        if not activate and not self.is_activated and admin and self._is_active:
            activate = u"BACKOFFICE override"

        # Activate if requested
        if activate:
            self._activate( activate, user )
        elif admin:
            self.add_history( "Backoffice update", user, save=False )

        # Set active flag off if end date has passed
        if not self.is_current:
            log.debug("Disabling APA, end date exceeded: %s -> %s", self, self.period_end)
            self.add_history( "License inactive, end date exceeded", save=False )
            self._is_active = False

        disable = kwargs.pop( '_disable', None )
        if disable is True:
            log.debug("Disabling APA forced: %s", self)
            self.add_history( "License disabled", save=False )
            self._is_active = False
        elif disable is False:
            log.debug("APA forced enable: %s", self)
            self.add_history( "License enabled", save=False )
            self._is_active = True

        super().save( *args, **kwargs )

        # Allow other areas to react to users that are part of the initial APA
        if admin:
            apa_update.send( sender=self.sandbox_id, apa=self )

    def _create_init( self, user, admin ):
        """
        Before APA is first saved, fixup state based on known relationships
        The admin flag indicates whether creation occurred in the admin
        """
        assert self.pa and self.account
        log.debug("Initializing APA: %s, %s -> %s", user, admin, self)

        if not admin:
            # Set purchase type based on criteria
            if self.coupon:
                self.purchase_type = 'C'
            else:
                self.purchase_type = 'F' if self.access_free else 'P'

        # Add historical info
        self.data.set( 'total_paid', str(self.access_price) )
        self.add_history( u"Initializing{}".format( u" paid" if not self.access_free
                             else ""), user, save=False )

    def _activate( self, info, user ):
        """
        Mark the APA as purchased; update purchase info and start date
        """
        log.debug("Activating APA: %s", self)
        self.is_activated = True

        # Setup time period by defining end date
        # End is either explicitly defined or set by PA time period
        self.period_start = now()
        if not self.period_end:
            end_date = self.get_period_end()
            if end_date:
                self.period_end = end_date

        # Only actually make active if the dates make sense
        if not self.period_end or ( self.period_end > self.period_start ):
            self._is_active = True

        # Save raw purchase info
        self.add_history( u"Activated: {}".format( info ), user, save=False )

    @property
    def access_tax( self ):
        """
        Total tax based on the current period price.
        """
        rv = Decimal('0')
        tax = self.account.get_tax()
        if tax:
            rv = Decimal( float( self.access_price ) *
                        tax.get( 'percent', float(0) ) )
        return rv

    @property
    def is_current( self ):
        """
        Is the APA in a valid time window
        """
        log.detail3("APA time check: %s -> end(%s)", self, self.period_end)
        return not self.period_end or self.period_end > now()

    @property
    def is_available( self ):
        """
        A user be added to an APA if it is active and has
        room in the user limit.
        """
        if self.is_active():
            if self.ga_users_max:
                return self.user_count < self.ga_users_max
            else:
                return True

    @property
    def has_more_uses( self ):
        """
        Has the APA exceeded allowed uses
        """
        if not self.is_activated:
            return True
        rv = not self.rules['one_time_use']
        if rv:
            max_uses = safe_int( self.rules['max_uses'] )
            if max_uses:
                rv = self.renewals < max_uses
        return rv

    def is_full( self, points=1 ):
        """
        Returns true no room remains based on any hard cap usage rules.
        If metering is turned on for points/users/time, see whether
        paygo is allowed (in which case there is always room) or
        whether any base usage is available.
        """
        points_room = not self.base_points
        if not points_room:
            if self.paygo_points:
                points_room = True
            else:
                available = self.base_points - self.rules.get( 'usage_points', 0 )
                points_room = available >= points

        active_users = self.rules.get( 'users_used', 0 )
        users_max = self.rules.get( 'active_users_max', 0 )
        if users_max and users_max <= active_users:
            users_room = False
        else:
            users_room = not self.base_users
            if not users_room:
                if self.paygo_users:
                    users_room = True
                else:
                    users_room = self.base_users > active_users

        seconds_room = not self.base_minutes
        if not seconds_room:
            if self.paygo_minutes:
                seconds_room = True
            else:
                seconds_room = ( self.base_minutes * 60
                                    ) > self.rules.get( 'usage_seconds', 0 )

        log.debug2("APA room test: %s -> p:%s u:%s t:%s", self,
                points_room, users_room, seconds_room)
        return not points_room or not users_room or not seconds_room

    def is_active( self, save=False, deep=False ):
        """
        Return if APA can be used
        HACK - If expired, save turns off the _is_active flag
        """
        rv = self._is_active
        if rv:
            rv = self.is_activated
            if rv:
                rv = self.is_current
                if rv:
                    rv = not self.is_full()
                    if rv and deep:
                        rv = self.account.is_active
        if save and self._is_active and not rv:
            self._is_active = False
            self.save()
        return rv

    def room_for_item( self, item ):
        """
        Returns true if room for the given item
        """
        return not self.is_full( item.points )

    def item_first_use( self, item, user ):
        """
        Called the first time a user accesses an item with the APA
        in the current access period, to support usage metering.
        """
        log.debug("APA points increment: %s -> %s", self, item.points)
        # Set every point
        points_used = self.data.get( 'usage_points', 0 )
        self.data.set( 'usage_points', points_used + item.points )
        # Only set user if not seen this period
        emails = self.data.get( 'usage_user_emails', [] )
        if not user.email in emails:
            emails.append( user.email )
            self.data.set( 'usage_user_emails', emails )
            self.data.set( 'usage_users', len(emails) )
        self.save()

    def item_seconds_use( self, item, user, seconds ):
        """
        Called whenever an item is accessed to support timed APAs
        """
        log.detail3("APA usue update: %s -> %s, %s", self, item, seconds)
        seconds_used = self.data.get( 'usage_seconds', 0 )
        self.data.set( 'usage_seconds', seconds_used + seconds )
        self.save()

    @property
    def purchase_type_lookup( self ):
        return self.PURCHASE_TYPE_LOOKUP.get( self.purchase_type )

    def apply_pa_override( self ):
        """
        If PA has control_apas set, override with values from PA
        """
        if self.pa.control_apas:
            for field in self.pa_control_fields:
                pa_map = self._pa_control_maps.get( field )
                if pa_map:
                    pa_value = pa_map( self )
                else:
                    pa_value = getattr( self.pa, field, None )
                if pa_value is not None:
                    setattr( self, field, pa_value )
    _pa_control_maps = {
        '_is_active': lambda apa: apa.pa.enabled,
        '_rules': lambda apa: apa._rules.update( apa.pa._rules ),
        }

    #--------------------------------------------------------------------
    # Connection to users

    @property
    def default_mode( self ):
        """
        Returns the default content delivery mode defined by account or sandbox
        """
        rv = self.sandbox.delivery_mode
        if self.account.is_group:
            account_override = self.account.group_account.delivery_mode
            if account_override:
                rv = account_override
        return rv

    @property
    @stash_method_rv
    def user_ids( self ):
        """
        Returns list of user IDs for optimized bulk operations
        or empty if no users assigned.
        """
        if not self.account.is_group or self.ga_license:
            return self.account.user_ids
        else:
            return list( self.ga_users.mpusing('read_replica')\
                            .values_list( 'user_id', flat=True ) )

    @property
    def user_count( self ):
        """
        Default is individual APA, update users attached to APA or GA
        """
        return len( self.user_ids )

    @property
    @stash_method_rv
    def user_info( self ):
        rv = u"Single user"
        if self.account.is_group:
            if self.ga_license:
                rv = u"All group users ({} current)".format( self.user_count )
            else:
                if self.user_count == 1:
                    first = self.ga_users.first()
                    if first:
                        rv = str( first )
                else:
                    rv = u"{} users".format( self.user_count )
                    if self.ga_users_max:
                        rv = u"{}, max: {}".format( rv, self.ga_users_max )
        return rv

    @stash_method_rv
    def user_attached( self, user ):
        """
        Check if user has access to the APA via user_accounts
        SCALE - group account checks require DB hit; consider custom DB call
        """
        au = get_au( user )
        if not au:
            return

        # For group accounts, check APA users or account users (group license)
        if self.account.is_group:
            if self.ga_license:
                return self.account.group_account.users.filter( id=au.pk ).exists()
            else:
                return self.ga_users.filter( id=au.pk ).exists()

        # For individual and shared accounts match user to primary account
        else:
            return self.account.primary_aus.filter( id=au.pk ).exists()


    def add_ga_user( self, user, force=False ):
        """
        Adds a user to APA if APA is valid, is for a group account,
        user has relationship, and the APA has room.
        Returns AU if the user is added OR already had access
        """
        au = get_au( user )
        if au:
            if ( force or self.is_active() ) and self.account.is_group:

                if self.account in au.accounts:
                    log.debug("GA APA user already tied to GA: %s -> %s", self, user)
                else:
                    ga = self.account.group_account
                    log.info2("GA APA migrating user: %s -> %s, %s",
                                user, ga, self)
                    ga.add_accountuser( au )

                if self.ga_license:
                    log.info2("GA APA add user, group APA: %s -> %s", self, user)
                    return au
                else:
                    if self.ga_users.filter( id=au.pk ).exists():
                        log.info2("GA APA add user, already in APA: %s -> %s",
                                    self, user)
                        return au
                    else:
                        if( not self.ga_users_max or
                                self.user_count < self.ga_users_max ):
                            log.info2("GA APA add user: %s -> %s", self, user)
                            self.ga_users.add( au )
                            self.clear_stash()
                            apa_add_users.send( sender=self.sandbox_id,
                                        apa=self, users=[user] )
                            return au

                    reason = "APA is full"
            else:
                reason = "GA is not viable"
        else:
            reason = "No AU for user"
        log.info("GA APA add user rejected: %s -> %s -> %s", self, user, reason)

