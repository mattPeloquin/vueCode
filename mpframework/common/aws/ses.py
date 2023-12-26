#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared SES code

    Most email interface is handled through Django
"""

from .. import log
from . import get_client


def get_ses():
    return get_client( 'ses' )


def verify_email( email ):
    """
    Start verification process for the given email against the root account
    """
    try:
        log.info("AWS - SES email verify: %s", email)

        return get_ses().verify_email_address( EmailAddress=email )

    except Exception:
        log.exception("SES email verify: %s", email)
