#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Pricing Option / SKU / Licensing option / PA (ProductAgreement)

    Represents a specific product offering that brings together content
    items and licensing. PAs are analogous to retail SKUs, and use
    'sku' as for the user to identify specific offerings.

    FUTURE - Add django-money and other support for L10 pricing
"""
import re
from decimal import Decimal
from django.db import models
from django.db.models import Q

from mpframework.common import constants as mc
from mpframework.common.model import CachedModelMixin
from mpframework.common.model.fields import YamlField
from mpframework.common.model.fields import mpDateTimeField
from mpframework.common.utils import now
from mpframework.common.utils.strings import intersection_comma_lists
from mpframework.common.cache import stash_method_rv
from mpframework.foundation.tenant.models.base import SandboxModel
from mpframework.content.mpcontent.tags import ContentTagMatchMixin

from ..access_period import AccessPeriodMixin
from ..access_pricing import AccessPricingMixin
from ..cache import cache_group_catalog
from .agreement import Agreement
from .pa_manager import PaManager


class PA( ContentTagMatchMixin, AccessPeriodMixin, AccessPricingMixin,
            CachedModelMixin, SandboxModel ):
    """
    PAs are called "Pricing options" in the UI and define a specific
    product offering/SKU.
    PAs are templates for creating APA/license instances:

      - Define the content to include in the APA
      - Set access period duration and price for APA
      - Are based Agreements, and can add/override license options
      - Optionally control some fields in existing APAs
      - Coupons override PA settings when APA created.

    Content access is granted by the existence of active APAs.
    PA/APA is checked each time users try to access content tied to PA/APA.
    The PA sets up the default license tag matches, access periods,
    pricing, and licensing rules used to create APAs.
    Pricing is only used for online purchases and automated payments;
    backoffice licenses can be created with no price/payments.

    PA attributes:

      - tag_matches, access_period, unit_price
        These core attributes are DB fields whose relationship to Agreements,
        APAs, and Coupons is handled by specific code.
        IF LEFT BLANK IN APA, WILL 'FOLLOW' PA CHANGES

      - Most other PA attributes/options are implemented in the license rules
        yaml field. These are effectively copied from Agreement, and then
        PA and Coupon rules are copied into APAs. Unlike the core attributes,
        APA rules don't 'follow' PA or Agreement rule changes once they
        have been opened in the admin - they are copied.

    The access period is ONLY used to calculate the next APA end date. It is
    used on APA/license creation and for subscriptions and other renewals.
    Backoffice actions can override the APA/license end date (and other options)
    at any time, which can change the license and user access.

    Access period usage defaults to providing unlimited access to all matched
    content for all users attached to the APA/license. This default approach
    of the system code is modified with Agreement rules.

    Pricing is used to drive automated payments and for reporting with
    backoffice invoicing. Total cost for an access period is calculated from
    the base unit price that represents cost for one 'sku unit' for one
    access period. Total price is then modified for any paygo pricing and
    potentially other Agreement rules.

    Once an APA/license is created, the APA/license usually lives on its own,
    but will follow some PA settings if control_apas is on.
    """

    # A unique (to sandbox) code for tracking the item
    sku = models.SlugField( db_index=True, allow_unicode=True,
                            max_length=mc.CHAR_LEN_UI_CODE,
                            verbose_name=u"SKU/URL" )

    # What license rules was this PO created with?
    agreement = models.ForeignKey( Agreement, models.CASCADE,
                                   verbose_name=u"License type" )

    # Overrides and additions to Agreement rules
    # HACK SCALE DB MIGRATE - manually add a FULLTEXT index for DB WHERE clauses
    _rules = YamlField( null=True, blank=True, db_column='rules' )

    # Toggle showing/availability of the PA
    enabled = models.BooleanField( default=True,
                                   db_column='is_active' )

    # When can this PA be seen/used?
    VISIBILITY = (
        ('A', u"All users"),
        ('C', u"Specific accounts"),
        ('N', u"EasyLinks only"),
        ('B', u"Backoffice only"),
        )
    visibility = models.CharField( max_length=1, choices=VISIBILITY, default='A',
                                   blank=False )

    # Short and long marketing information
    # Name defaults to SKU, while _description defaults to price
    _name = models.CharField( blank=True, max_length=mc.CHAR_LEN_UI_CODE,
                              verbose_name=u"Short name", db_column='name' )
    _description = models.TextField( blank=True, verbose_name=u"Display text",
                                     db_column='description' )

    # Does PA control existing licenses
    control_apas = models.BooleanField( default=False,
                                        verbose_name=u"Overwrite licenses" )

    # Start/stop for the PA itself, supports running special promotions
    pa_starts = mpDateTimeField( blank=True, null=True )
    pa_expires = mpDateTimeField( blank=True, null=True )

    # Limit use of the PA to account subsets based on comma-delimited account codes
    account_codes = models.CharField( max_length=mc.CHAR_LEN_UI_LINE, blank=True )

    # Internal staff notes and searchable staff codes
    notes = models.CharField( max_length=mc.CHAR_LEN_DB_SEARCH, blank=True )

    class Meta:
        verbose_name = u"Pricing option"
        unique_together = ( 'sandbox', 'sku' )

    objects = PaManager()

    select_related = ( 'agreement' ,)
    select_related_admin = select_related + ()

    lookup_fields = ( 'id__iexact', 'sku__icontains',
                '_description__icontains' )

    _clone_fixups = (
        ( 'STRING', 'sku' ),
        )

    def __str__( self ):
        if self.dev_mode:
            return "{}(pa{})".format( self.name, self.pk )
        return str( self.name )

    @property
    def cache_group( self ):
        return cache_group_catalog( self.sandbox_id )

    @property
    def dict( self ):
        return {
            'id': self.pk,
            'sku': self.sku,
            'name': self.name,
            'description': self.description,
            'visibility': self.visibility,
            'price': self.access_price,
            }

    def clone( self, **kwargs ):
        """
        Make sure agreements get included in cloned PAs
        FUTURE - ONLY PA CLONING OF SYSTEM AGREEMENTS is implemented now
        """
        kwargs['_includes_'] = [ 'agreement' ]
        return super().clone( **kwargs )

    @staticmethod
    def available_Q():
        return (
            ( Q( pa_starts__lt=now() ) | Q( pa_starts__isnull=True ) ) &
            ( Q( pa_expires__gt=now() ) | Q( pa_expires__isnull=True ) ) &
            ( Q( access_end__gt=now() ) | Q( access_end__isnull=True ) ) &
            Q( enabled=True )
            )

    @staticmethod
    def is_free_Q():
        return (
            Q( _rules__icontains='access_free: true' ) |
            ( ( Q( _unit_price__lte=0 ) | Q( _unit_price__isnull=True ) ) &
              ( Q( _paygo_price__lte=0 ) | Q( _paygo_price__isnull=True ) ) &
               ~Q( _rules__icontains='initial_price' )
               )
            )

    @staticmethod
    def is_subscription_Q():
        return Q( _rules__icontains='auto_renew: true' )

    @staticmethod
    def is_reusable_Q():
        return ~Q( _rules__icontains='one_time_use: true' )

    @staticmethod
    def in_use_Q():
        return Q( apas___is_active=True ) & Q( apas__period_end__gt=now() )

    @property
    def unit_price( self ):
        return self._unit_price or Decimal(
                    self.rules.get( 'unit_price', '0' ) )
    @property
    def paygo_price( self ):
        return self._paygo_price or Decimal(
                    self.rules.get( 'paygo_price', '0' ) )

    @property
    @stash_method_rv
    def rules( self ):
        """
        Combine Agreement and PA rules
        """
        rv = self.agreement.rules
        rv.update( self._rules )
        return rv

    @property
    def available( self ):
        """
        Is the PA available to create new APAs?
        """
        return self.enabled and self.dates_ok

    @property
    def dates_ok( self ):
        _now = now()
        return ( ( self.access_end > _now if self.access_end else True ) and
                 ( self.pa_expires > _now if self.pa_expires else True ) and
                 ( self.pa_starts < _now if self.pa_starts else True ) )

    @property
    def active_apa_count( self ):
        """
        Number of active licenses based on the PA
        """
        return self.apas.filter( _is_active=True, period_end__gt=now() ).count()

    @property
    def visible_to_all( self ):
        return self.visibility in ['A']

    @property
    def visible_to_links( self ):
        return self.visibility in ['A','N']

    def visible_to_account( self, account ):
        return self.visible_to_all or (
                self.visibility in ['C'] and intersection_comma_lists( account.codes, self.account_codes ) )

    @property
    def name( self ):
        """
        Short display name (option to override SKU)
        """
        return self._name if self._name else self.sku

    @property
    @stash_method_rv
    def description( self ):
        """
        Returns a basic description with any tag replacements filled out.
        Tags are defined in double brackets, as defined in the
        tag_replacements lookup below.
        This is not perfect, intended to provide an ok default, but
        it is expected that _description will normally be filled in.
        """
        if not self._description:
            # Do a default price description that handles most cases reasonably
            price = u"${}".format( self.unit_price ) if self.unit_price else u"Free"
            initial = self.rules['initial_price']
            startup = u" (${} startup)".format( initial ) if initial else ""
            prefix = u"every " if self.is_subscription else u"for "
            period = self.access_period_desc( use_prefix=prefix )
            content = "" if self.includes_all else u" for {}".format(
                        self.tag_matches )
            return "{} {}{}{}".format( price, period, startup, content )

        def tag_replacements( match ):
            tag = match.group(1)
            if tag == 'price':
                return u"${}".format( self.access_price
                            ) if self.access_price else u"Free"
            if tag == 'period':
                return self.access_period_desc()
            if len( tag ) > 1:
                time_desc = self.access_period_desc( tag[:-1], use_prefix=False )
                if time_desc:
                    return time_desc
            return ""

        return self.description_tag_re.sub( tag_replacements, self._description )

    description_tag_re = re.compile('{{\s*(.*?)\s*}}')
