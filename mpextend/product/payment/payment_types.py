#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Configure payment types and map onto flows.
    Data here is dependent on code; anything configurable for a deployment
    should be added to MP_ROOT['PAYMENT'] settings.
"""

from .flows import paypal_nvp
from .flows import stripe_connect


PAYMENT_TYPES = {

    'stripe_connect': {
        'service': 'stripe_connect',
        'name': u"Stripe",
        'flow': stripe_connect,
        },

    'paypal_nvp': {
        'service': 'paypal_nvp',
        'name': u"Paypal Express",
        'flow': paypal_nvp,
        'client': u"PayPal",
        },

    }
