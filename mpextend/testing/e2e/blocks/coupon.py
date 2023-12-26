#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Coupon block support
"""

from mpframework.testing.e2e.data import get_unique_dict
from mpframework.testing.e2e.data import get_unique_data
from mpframework.testing.e2e.blocks._base import SystemTestBlock

from ..data import *


class CouponBlock( SystemTestBlock ):

    def __init__( self, stc, data=None, ctype=None, **kwargs ):
        """
        Add support for different types of content
        If type is provided, set here, it is assumed that either the content
        is already created with that type, or will only create that type
        """
        self.type = ctype
        super(CouponBlock, self ).__init__( stc, data, **kwargs )

    def create_item ( self, data=None ):

        self.stc.go_menu('catalog','coupons')
        self.stc.go_anchor( 'Add Coupon' )

        if not data:
            data = get_unique_dict( COUPON )

        self.update_data( data )

        self.stc.get_id('mpsave').click()

        return self
