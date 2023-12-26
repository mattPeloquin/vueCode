#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Coupon model
"""
from django.db import models
from django.db.models import Q

from mpframework.common import log
from mpframework.common import constants as mc
from mpframework.common.utils import now
from mpframework.common.utils.strings import intersection_comma_lists
from mpframework.common.model.fields import mpDateTimeField
from mpframework.common.model.fields import TruncateCharField
from mpframework.common.model.fields import YamlField
from mpframework.foundation.tenant.models.base import SandboxModel
from mpframework.content.mpcontent.tags import ContentTagMatchMixin

from ..access_period import AccessPeriodMixin
from .pa import PA
from .coupon_manager import CouponManager


class Coupon( ContentTagMatchMixin, AccessPeriodMixin, SandboxModel ):
    """
    Coupons extend/modify PA terms
    They may be typed in or used through links. There are two modes,
    tying to a specific PA, or being a general modifier to any PA.
    The provide usage counting on the coupon itself.

    The use of a coupon creates a new APA. Price, end date, license tags,
    points some rules may be modified from the original PA.
    Although technically possible to override all PA attributes, coupon
    features are limited (slightly) to reduce confusion and edge cases.

    Coupon codes can be used either as URL slugs or traditional typed in
    codes disseminated to end users to modify purchase options.
    The lifetime and usage of coupon can be configured.
    Coupon codes cannot be changed once created; this prevents confusion
    regarding history, uses, etc. (which occur when reusing a coupon record).
    Many scenarios involve using a similar coupon with a code that changes
    over time; this is supported by copying.
    """

    # Code used to validate the coupon (also default URL)
    # Unique to the sandbox and once created a coupon code cannot be changed
    # To reuse a coupon, dates, etc. can be updated
    code = models.SlugField( db_index=True, allow_unicode=True,
                max_length=mc.CHAR_LEN_UI_CODE, verbose_name=u"Code/URL" )

    # The PA this coupon applies to
    # If blank, coupon is global to sandbox or defined by license tag matches
    pa = models.ForeignKey( PA, models.CASCADE,
                null=True, blank=True, related_name='coupons',
                verbose_name=u"Pricing option" )

    # Coupon price adjustments
    # None/Blank is no adjustment
    # 0 is free, between 0 and 1 is a percent discount, 1 means same price
    # Above 1 is an absolute unit price
    # This means coupons can't define a price of $1 or less, which should be ok
    unit_price = models.DecimalField( decimal_places=2, max_digits=7,
                blank=True, null=True )
    paygo_price = models.DecimalField( decimal_places=2, max_digits=7,
                blank=True, null=True )

    # Overrides and additions to some Agreement rules
    # HACK SCALE DB MIGRATE - manually add a FULLTEXT index for DB WHERE clauses
    _rules = YamlField( null=True, blank=True, db_column='rules' )

    # Toggle coupon on and off
    enabled = models.BooleanField( default=True )

    # Absolute date after which COUPON will not be honored
    coupon_expires = mpDateTimeField( blank=True, null=True )

    # Tracking of uses and optional cap on the number of uses
    uses_max = models.IntegerField( blank=True, null=True )
    uses_current = models.IntegerField( default=0, blank=True, null=True )

    # Optional description (to override PA)
    _description = models.TextField( blank=True, db_column='description',
                                     verbose_name=u"Description" )

    # Limit use of the PA to account subsets based on comma-delimited account codes
    account_codes = models.CharField( blank=True, max_length=mc.CHAR_LEN_UI_LINE )

    # Programmatic history of updates to coupon, including rotating code
    history = TruncateCharField( blank=True, max_length=mc.CHAR_LEN_DB_SEARCH )

    # Staff notes used in admin
    notes = models.CharField( blank=True, max_length=mc.CHAR_LEN_DB_SEARCH )

    class Meta:
        verbose_name = u"Coupon"
        unique_together = ('sandbox', 'code')

    objects = CouponManager()

    select_related = ( 'pa' ,)
    select_related_admin = select_related

    _clone_fixups = (
        ( 'FK', ( PA, 'pa', 'sku' ) ),
        ( 'STRING', 'code' ),
        )

    def __str__( self ):
        return "{}:{},{}:{}".format( self.code, self.unit_price,
                    self.paygo_price, self.access_period )

    @property
    def dict( self ):
        return {
            'id': self.pk,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'pa': self.pa.pk if self.pa else None,
            'period': self.access_period,
            'unit_price': self.unit_price,
            'paygo_price': self.paygo_price,
            'available': self.available,
            'access_end': self.access_end,
            'coupon_expires': self.coupon_expires,
            }

    @staticmethod
    def is_active_Q():
        return (
            Q( enabled=True ) &
            ( Q( access_end__gt=now() ) | Q( access_end__isnull=True ) ) &
            ( Q( coupon_expires__gt=now() ) | Q( coupon_expires__isnull=True ) )
            )

    @staticmethod
    def search_Q( pa=None, free=False, active=True ):
        rv = [ Coupon.is_active_Q() ] if active else []
        if free:
            rv.append( Q( _rules__icontains='access_free: true' ) |
                        Q( unit_price__lte=0 ) )
        # Support filtering on items that are PA only, or a given PA
        # plus all general items, general items only, or all
        if pa is True:
            rv.append( Q( pa__isnull=False ) )
        elif pa is False:
            rv.append( Q( pa__isnull=True ) )
        elif pa:
            rv.append( Q( pa=pa ) | Q( pa__isnull=True ) )
        return rv

    @property
    def rules( self ):
        return self._rules

    @property
    def available( self ):
        """
        Is the coupon enabled and within valid params
        """
        return self.enabled and self.uses_ok and self.dates_ok

    @property
    def uses_ok( self ):
        log.debug2("Coupon uses/max: %s -> %s / %s", self, self.uses_current, self.uses_max)
        return (self.uses_current < self.uses_max) if self.uses_max else True

    @property
    def dates_ok( self ):
        _now = now()
        return ( ( self.access_end > _now if self.access_end else True ) and
                 ( self.coupon_expires > _now if self.coupon_expires else True ) )

    def account_ok( self, account ):
        log.debug2("Coupon account check: %s, %s -> %s", self, self.account_codes, account )
        return ( not account or
            not self.account_codes or
            intersection_comma_lists( account.codes, self.account_codes )
            )

    @property
    def tag_matches( self ):
        """
        Tags used to match content for this coupon.
        """
        pa_matches = self.pa.tag_matches if self.pa else ''
        return self._tag_matches if self._tag_matches else pa_matches

    @property
    def name( self ):
        return( self.pa.name if self.pa else self.code )
    @property
    def description( self ):
        return( self._description if self._description else
                self.pa.description if self.pa else
                self.name )

    def price_adjust( self, apo ):
        """
        Implement coupon price adjustments on the given PA or APA
        """
        log.debug("Coupon price adjust: %s -> %s", apo, self)
        self._price_adjust( apo, 'unit_price' )
        self._price_adjust( apo, 'paygo_price' )
        log.info2("COUPON %s: %s", self, apo.access_price)

    def _price_adjust( self, apo, field_name ):
        """
        Implement coupon price adjustments on the given PA or APA
        """
        log.debug("Coupon price adjust: %s -> %s", apo, self)
        price_adj = getattr( self, field_name )
        if ( price_adj is None or
                price_adj == 1 or
                price_adj < 0 ):
            return
        apo_field = '_' + field_name
        if price_adj < 1:
            price = getattr( apo, apo_field ) * price_adj
        else:
            price = price_adj
        setattr( apo, apo_field, price )
