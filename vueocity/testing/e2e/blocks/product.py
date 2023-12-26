#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Represents a simplified content/catalog combination
    created with the EasyVue product UI
"""
import random

from mpframework.common.utils.strings import make_tag
from mpframework.testing.e2e.blocks._base import SystemTestBlock
from mpframework.testing.e2e.blocks.content import ContentBlock
from mpframework.testing.e2e.data import get_unique_dict
from mpframework.testing.e2e.data import *
from mpextend.testing.e2e.blocks.pricing import PricingBlock
from mpextend.testing.e2e.blocks.coupon import CouponBlock
from mpextend.testing.e2e.data import *


_PROD_CONTENT = ['file', 'video', 'audio']


class ProductBlock( SystemTestBlock ):
    """
    Brings together content and catalog data for items created
    using the EasyVue add product screen

    Product blocks don't hold their own data, instead they use data
    from their content and catalog blocks
    """

    def verify_portal( self ):
        """
        Verify product data in portal
        """
        self.content.verify_portal()
        self.pricing.verify_portal()
        self.pricing_trial.verify_portal()

    #---------------------------------------------------------------
    # Methods below can only use used when a staff user is active

    def create_item( self, content=None, pricing=None, coupon=None ):
        """
        Create content and catalog data from EasyVue Add product screen,
        either using either specific data, or defaults. The tags for
        the content and pricing options must match up
        """

        # Setup content type and detailed content; only certain content types
        # can be created as a product
        ctype = random.choice( _PROD_CONTENT )
        if not content:
            content = get_unique_dict( CONTENT )
            content.update( get_unique_data( CONTENT_TYPES[ ctype ] ) )
        content['_name'] += ' product'
        content['tag'] = make_tag( content['_name'] )
        self.content = ContentBlock( self.stc, content, ctype, create=False )

        # Add product creates both a purchase and a trial purchase option,
        # create test objects for both
        if not pricing:
            pricing = get_unique_dict( PRICING )
        pricing['sku'] = make_tag( self.content.data['_name'], under=True, lower=True, max_len=24 )
        self.pricing = PricingBlock( self.stc, pricing, create=False )
        pricing_trial = pricing.copy()
        pricing_trial['sku'] += '_trial'
        self.pricing_trial = PricingBlock( self.stc, pricing_trial, create=False )

        # Coupon is only created sometimes
        self.coupon = None
        if not coupon:
            count = random.randint( 1, 2 )
            if count == 1:
                coupon = get_unique_dict( COUPON )
        if coupon:
            self.coupon = CouponBlock( self.stc, coupon, create=False )

        # Create the items through the add product screen
        self.stc.go_menu('easy', 'add-product')
        self.stc.get_id('id_name').send_keys( self.content.data['_name'] )
        self.stc.get_id('id_price').send_keys( self.pricing.data['price'] )
        self.stc.get_id('id_trial_min').send_keys( self.pricing.data['time'] )
        self.coupon and self.stc.get_id('id_coupon_code').send_keys(
                            self.coupon.data['code'])
        self.stc.upload_file( 'id_content_file', self.content.file_mapping[1] )
        if self.content.data.get('image1'):
            self.stc.upload_file( 'id_image', self.content.data['image1'] )
        self.stc.get_name('add_product').click()
        self.stc.wait_point()

        # If the screen has changed to the portal, the add was successful
        self.stc.get_css('.es_portal')
        self.stc.l("CREATED PRODUCT: %s -> %s", content, pricing)

        return self

    def update( self, content=None, pricing=None, pricing_trial=None ):
        """
        Fill out all content and catalog data using admin staff screens
        """
        self.content.update_admin( content )
        self.pricing.update_admin( pricing )
        self.pricing_trial.update_admin( pricing_trial )
        return self

    def verify_admin( self, full=False ):
        """
        Verify the product block data in admin screens, which is a subset
        of the available data
        """
        self.content.verify_admin( None if full else [ 'name', 'content_file' ] )
        self.pricing.verify_admin()
        self.pricing_trial.verify_admin()
