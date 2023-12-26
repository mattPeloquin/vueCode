#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    EasyVue product creation
"""

from ..blocks import ProductBlock


def new_products( stc, number, **kwargs ):
    """
    Returns list with the given number of ProductBlocks, with
    optional verification that product was created
    """
    rv = []
    verify = kwargs.pop( 'verify', False )
    for count in range( 0, number ):
        pb = ProductBlock( stc, **kwargs )
        if verify:
            pb.verify_admin()
        rv.append( pb )
    return rv

def edit_content( stc, products ):
    """
    Add all data into admin, also making some edits to and storing in block data
    """
    stc.go_menu('content', 'content-items')
    for pb in products:
        data = pb.content.data
        stc.go_anchor( data['_name'] )
        data_update = {}
        for field in data:
            if field.startswith('text'):
                text = data[ field ].split('->')
                updates = ' -> Updated:{}'.format( int(text[1].split(':')[1]) + 1
                                ) if len( text ) > 1 else ''
                data_update[ field ] = '{}{}'.format( text[0], updates )
        pb.content.update_data( data_update )
        stc.get_id('mpsave').click()

def edit_pricing( stc, products ):
    """
    Update pricing and coupon options from product creation
    """
    stc.go_menu('catalog', 'pricing-options')
    for pb in products:
        stc.go_anchor( pb.pricing.data['sku'] )
        stc.get_id('id_unit_price').send_keys( pb.pricing.data['price'] )
        stc.get_id('id_periods').send_keys( pb.pricing.data['time'] )
        stc.get_id('mpsave').click()


    """ TESTWORK - finish coupon pricing

    self.go_menu('catalog', 'coupons')
    for pb in products:
        self.go_anchor(pb.content.data['_name'])
        self.get_id('id_form-0-unit_price').send_keys(pb.catalog.data['price'])
        self.get_id('id_form-0-access_period').send_keys(pb.catalog.data['ADJ'])
        self.get_id('mpsave').click()
    """

def edit_coupon ( stc, coupons ):
    stc.go_menu('catalog', 'coupons')
    stc.go_anchor('Add Coupon')
    stc.send_keys()
    stc.get_id('mpsave').click()
