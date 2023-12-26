#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Pricing blocks handle pricing options (POs), which are
    also known as PA/PA and SKUs
"""

from mpframework.testing.e2e.data import get_unique_dict
from mpframework.testing.e2e.blocks._base import SystemTestBlock

from ..data import *


class PricingBlock( SystemTestBlock ):

    def verify_portal( self ):

        # TESTWORK - decide how to verify in the portal

        pass

    #-----------------------------------------------------------
    # Methods below can only use used with staff

    def create( self, data=None ):
        """
        Create pricing option from data
        """
        if not data:
            data = get_unique_dict( PRICING )
        return self.update_admin( data )

    def go_edit( self, portal=False ):
        """
        Go to the admin edit page for the content
        """
        self.stc.go_menu('catalog', 'pricing-options')
        self.stc.go_anchor( self.data['sku'] )

        # TESTWORK NOW - add support for pagination/search when list is long
