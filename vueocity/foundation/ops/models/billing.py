#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Provider billing support
"""
from django.db import models

from mpframework.common import log
from mpframework.common import constants as mc
from mpframework.common.model.fields import mpDateTimeField
from mpframework.common.model.fields import TruncateCharField
from mpframework.foundation.tenant.models.base import TenantManager
from mpframework.foundation.tenant.models.base.provider import ProviderModel


class Invoice( ProviderModel ):
    """
    Billing events and history for the provider

    Not intended to provide full GL capabilities, but
    will support some notion of whether the account is current
    and supporting adjustments on the bill.
    """

    STATE = (
        ('created', u"Invoice created in system"),
        ('submitted', u"Submitted to provider"),
        ('paid', u"Fully paid"),
        ('review', u"In review"),
        )
    state = models.CharField( max_length=16, choices=STATE, default='created' )

    """
    Open field that describes the bill

    This will include period, items, pricing, discount, terms, etc.
    Generated automatically or manually, the information is not rigidly
    tied back to system data.
    For example, for monthly user billing, the description should have
    the active user metrics, but as a snapshot in item; they will normally
    match future active user reports that look back to that period, but
    there may be data discrepancies that occur after description is made.
    """
    description = TruncateCharField( max_length=mc.CHAR_LEN_DB_SEARCH )

    # Amount, plus any tax, broken out as sent to payment like Paypal
    amount = models.DecimalField( decimal_places=2, max_digits=7 )
    tax = models.DecimalField( decimal_places=2, max_digits=7 )

    # The invoice or other code used in Paypal or external billing
    external_id = TruncateCharField( max_length=mc.CHAR_LEN_UI_LONG, blank=True )

    # Dates for the bill logistics
    # Dates related to billing period, etc. are captured in the description
    date_sent = mpDateTimeField( null=True, blank=True )
    date_paid = mpDateTimeField( null=True, blank=True )

    # Programmatic history of updates to billing item
    history = TruncateCharField( max_length=mc.CHAR_LEN_DB_SEARCH, blank=True )

    # Root notes
    notes = models.CharField( max_length=mc.CHAR_LEN_DB_SEARCH, blank=True )

    objects = TenantManager()

    def __str__( self ):
        return u"Invoice({})".format( self.pk )

    class Meta:
        app_label = 'ops'
