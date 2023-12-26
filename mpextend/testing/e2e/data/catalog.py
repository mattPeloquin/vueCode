#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Data templates for pricing options, coupons, catalog items
"""


PRICING = {

    'ONE_TIME_PURCHASE': {
        'price': '{price}',
        'time': '{time}',
        'ADJ': '{yo}',
        'sku': '{sku}'
        },

    }

LICENSES = {

    'CREATION': {
        'Add_License' : '{Add_License}',
    },
}

COUPON = {

    'DISCOUNT': {
        'code': 'c-{}',
        'unit_price': '{int}',
        'uses_max': '{int}',
        },

    }