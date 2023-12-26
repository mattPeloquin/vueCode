#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Payment flows are groupings of code for specific external
    solutions. Depending on the payment service, these are
    typically shared code, API calls, and sub-views.

    PORTIONS OF FLOW MODULES ARE DUCK-TYPED
"""

from . import paypal_nvp
from . import stripe_connect
