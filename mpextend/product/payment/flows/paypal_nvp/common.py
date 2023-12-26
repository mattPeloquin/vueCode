#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared Paypal code
"""
import requests
from urllib.parse import parse_qs
from django.conf import settings

from mpframework.common import log
from mpframework.common.logging.utils import remove_secrets


ACCOUNT_NAME = 'paypal_account'
paypal_nvp = settings.MP_ROOT['PAYMENT']['paypal_nvp']


def call_paypal_nvp( data ):
    """
    Make call to PayPal, adding default info used in every call.
    Returns None if there is a problem making the call to PayPal,
    otherwise returns dict of whatever PayPal returns.
    """
    data.update({
        'VERSION': '119',
        'USER': paypal_nvp['username'],
        'PWD': paypal_nvp['password'],
        'SIGNATURE': paypal_nvp['signature'],
        })
    log.info_on() and log.info2("PAY PAYPAL CALL: %s -> %s",
            paypal_nvp['url_api'], remove_secrets( data ) )
    try:
        response = requests.post( paypal_nvp['url_api'], data=data,
                    timeout=paypal_nvp['timeout'] )
    except Exception:
        log.exception("Problem calling Paypal")
    else:
        # Paypal body is same URL encode as querystrings
        parsed_response = parse_qs( response.text )
        log.info_on() and log.info2("PAY PAYPAL RESPONSE: %s", parsed_response)
        return parsed_response


def money_encode( value ):
    # Put dollar values into consistent format string for paypal
    return "{0:.2f}".format( float(value) )

def date_encode( date ):
    return date.strftime('%Y-%m-%dT%H:%M:%SZ')
