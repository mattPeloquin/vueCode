#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Pricing and payment logic shared between PA/APA

    Polymorphic PA/APA behavior refers to APOs (Access Pricing Objects)
"""
from decimal import Decimal
from django.db import models

from mpframework.common.cache import stash_method_rv


class AccessPricingMixin( models.Model ):
    """
    Pricing is based on rules, and may vary between the template
    pricing configured in PAs, and the APA current access period.
    """

    # Per-period, per-unit price
    # Blank means no adjustment, 0 is free
    _unit_price = models.DecimalField( decimal_places=2, max_digits=7,
                                       blank=True, null=True,
                                       db_column='unit_price',
                                       verbose_name=u"Base price" )

    # Incremental usage paygo pricing
    # Blank means cap instead of paygo for any provided metering limits
    _paygo_price = models.DecimalField( decimal_places=2, max_digits=7,
                                        blank=True, null=True,
                                        db_column='paygo_price',
                                        verbose_name=u"PayGo price" )
    class Meta:
        abstract = True

    @property
    def access_price( self ):
        """
        Provides exact or approximate price for PA/APA
        For APA with units and usage an exact price can be calculated; otherwise
        an estimate based on 1 unit and usage access price is provided.
        """
        return self.base_price + self.paygo_charge + self.additional_charge
    @property
    def base_price( self ):
        units = abs( getattr( self, 'units', 1 ) )
        return units * Decimal( self.unit_price or '0' )
    @property
    def paygo_charge( self ):
        usage = getattr( self, 'paygo_units', 1 )
        return usage * Decimal( self.paygo_price or '0' )
    @property
    def additional_charge( self ):
        rv = Decimal('0')
        renewals = getattr( self, 'renewals', 0 )
        if not renewals:
            rv += Decimal( self.rules.get( 'initial_price', '0' ) )
        return rv

    @property
    @stash_method_rv
    def access_free( self ):
        return self.rules['access_free'] or self.access_price <= 0

    @property
    @stash_method_rv
    def access_no_payment( self ):
        """
        If there's no need to charge payment, some flow can be altered
        """
        return self.rules['backoffice_payment'] or self.access_free

    @property
    @stash_method_rv
    def is_subscription( self ):
        return bool( self.rules['auto_renew'] )

    @property
    @stash_method_rv
    def is_trial( self ):
        return bool( self.rules['is_trial'] )
