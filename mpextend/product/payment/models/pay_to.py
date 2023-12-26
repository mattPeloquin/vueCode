#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    PayTo model receives payment for a seller of content licenses.
"""
from django.db import models

from mpframework.common import constants as mc
from mpframework.common.model.fields import YamlField
from mpframework.foundation.tenant.models.base.provider import ProviderModel
from mpframework.foundation.tenant.models.provider import Provider
from mpframework.foundation.tenant.models import Sandbox
from mpextend.product.account.models import GroupAccount

from ..payment_types import PAYMENT_TYPES
from .pay_to_manager import PayToManager


class PayTo( ProviderModel ):
    """
    PayTo is a configuration model that holds external payment service
    information for sellers (provider, site, or account).

    PayTo instances are 1:M with PayUsing models, which make payments
    (both interactive and recurring) to the PayTo.
    Once created, the PayTo instance sets a particular payment
    scenario (e.g., specific Stripe account); the payment type
    (Stripe, Paypal, etc.) is immutable.

    Support for different payment providers is built into payment
    api and view code; this model holds information used by
    that code but should have no external service-specific code.
    """

    # PayTo is tied to one of these levels
    # If more than one is used, most specific trumps.
    # GenericForeignKey isn't used because it is clunky and the logic
    # related to these relationships is not completely polymorphic.
    _provider = models.ForeignKey( Provider, models.CASCADE,
                db_column='provider_id', related_name='pay_to' )
    sandbox = models.ForeignKey( Sandbox, models.CASCADE,
                blank=True, null=True, related_name='pay_to',
                verbose_name=u"Site" )

    # Type of purchase transaction the APA represents
    # Payment code for different services is tied to these types
    payment_type = models.CharField( db_index=True, max_length=16,
                choices=[ (n, v['name']) for n, v in PAYMENT_TYPES.items() ] )

    # Link to payment account
    # Assume payment services will have an ID that allows linkage;
    # PayTos are only active if this is valid.
    # DB-indexed field because it may be used to lookup PayTo to determine
    # tennancy when OAuth or webhooks are called from the external provider.
    service_account = models.CharField( db_index=True, blank=True,
                max_length=mc.CHAR_LEN_UI_DEFAULT )

    # External payment service configuration
    # The configuration details schema shifts based on payment service
    payment_config = YamlField( null=True, blank=True )

    # FUTURE - support marketplace scenarios
    seller_account = models.ForeignKey( GroupAccount, models.CASCADE,
                blank=True, null=True, related_name='pay_to' )

    objects = PayToManager()

    # Account user is always referenced with user
    select_related = ( '_provider', 'sandbox', 'seller_account' )
    select_related_admin = select_related + ()

    def __str__( self ):
        if self.dev_mode:
            return "payto({}-{})".format( self.pk, self.name )
        return self.name

    def save( self, *args, **kwargs ):
        super().save( *args, **kwargs )

    @property
    def dict( self ):
        return {
            'id': self.pk,
            'service': self.payment_type,
            'service_account': self.service_account,
            'name': self.get_payment_type_display(),
            'config': self.payment_config,
            }

    @property
    def is_active( self ):
        return bool( self.service_account )

    @property
    def seller( self ):
        return self.seller_account or self.sandbox or self.provider

    @property
    def name( self ):
        return self.seller.name
