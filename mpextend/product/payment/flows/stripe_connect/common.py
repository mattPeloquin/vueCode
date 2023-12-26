#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared Stripe code
"""
from django.conf import settings
import stripe


ACCOUNT_NAME = 'stripe_account'
SC = settings.MP_ROOT['PAYMENT']['stripe_connect']

stripe.api_key = SC.get('secret_key')

# Setup request defaults
client = stripe.http_client.RequestsClient( timeout=SC.get('timeout') )
stripe.default_http_client = client
stripe.max_network_retries = 2


def money_encode( value ):
    # Strip takes cents as integer
    return int( value * 100 )
