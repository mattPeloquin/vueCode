#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    PayUsing model sends account payment for content licenses.
"""
from django.db import models

from mpframework.common.model.fields import YamlField
from mpframework.foundation.tenant.models.base import SandboxModel
from mpextend.product.account.models  import Account

from .pay_to import PayTo
from .pay_using_manager import PayUsingManager


class PayUsing( SandboxModel ):
    """
    Captures information Accounts use to pay for APAs for a
    particular Payment service type (Stripe, PayPal, etc.).

    Payment details are stored on the payment service. This model
    holds information returned from the services used for
    recurring payments and follow-on activities.

    Each PayUsing ties an Account to a PayTo instance. The connection
    between the Account and PayTo is immutable after creation.

    apa_payments holds payment information for each APA purchased,
    which can be one-off or recurring subscriptions. The information
    held for payments is determined by the payment_type.

    Most PayUsing records are created automatically when a user selects a
    payment option during an access purchase. Multiple PayUsings are created
    when different payment options are selected.
    """
    account = models.ForeignKey( Account, models.CASCADE,
                                 related_name='pay_using' )
    pay_to = models.ForeignKey( PayTo, models.CASCADE,
                                related_name='pay_usings' )

    # Stores information for each APA payment users have setup between
    # the account the PayTo payment_type.
    _apa_payments = YamlField( null=True, blank=True, db_column='apa_payments' )

    objects = PayUsingManager()

    # Account user is always referenced with user
    select_related = ( 'account', 'pay_to' )
    select_related_admin = select_related + ()

    def __str__( self ):
        if self.dev_mode:
            return "payusing({}-{})".format( self.pk, self.name )
        return self.name

    def save( self, *args, **kwargs ):
        super().save( *args, **kwargs )

    @property
    def name( self ):
        return self.account.name

    """
    APA payment interface
    Since DB lookup isn't needed, manage APA payment info as Yaml field vs.
    a through table between APA and PayUsing.
    The data for each APA record is managed by the payment_type.
    """
    def get_apa_payment( self, apa ):
        return self._apa_payments[ apa.id ]

    def set_apa_payment( self, apa, info ):
        self._apa_payments[ apa.id ] = info
