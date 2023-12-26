#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    PayEvent model captures payment history
"""
from django.db import models

from mpframework.common import log
from mpframework.common.model.fields import YamlField
from mpframework.foundation.tenant.models.base import SandboxModel
from mpframework.foundation.tenant.models.base import TenantManager
from mpextend.product.account.models import APA

from .pay_to import PayTo
from .pay_using import PayUsing


class PayEvent( SandboxModel ):
    """
    Captures history of payment from a PayUsing to a PayTo for an APA.

    The database of record and all edge case management for payments
    is handled on external service payments platforms. This data is
    intended for easy in-situ history of nominal payment events and
    some key pathways such as a failed subscription payment.
    """
    pay_using = models.ForeignKey( PayUsing, models.CASCADE,
                                   related_name='pay_events' )
    pay_to = models.ForeignKey( PayTo, models.CASCADE,
                                related_name='pay_events' )

    # that are stored on the service
    apa = models.ForeignKey( APA, models.CASCADE,
                             related_name='pay_events' )

    # Semi-structured data from events
    history = YamlField( null=True, blank=True )

    objects = TenantManager()

    # Account user is always referenced with user
    select_related = ( 'pay_using', 'pay_to', 'apa' )
    select_related_admin = select_related + ()

    def __str__( self ):
        if self.dev_mode:
            return "payevent({}-{})".format( self.pk, self.name )
        return self.name

    def save( self, *args, **kwargs ):
        super().save( *args, **kwargs )

    @property
    def name( self ):
        return self.apa.name
