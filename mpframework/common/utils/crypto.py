#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    String utilities
"""
from django.conf import settings
from django.utils.crypto import get_random_string


def get_random_key( length=8, prefix='', suffix='' ):
    """
    Support centralized creation of keys used for sessions, caching, etc.
    Prefixing, etc. is for human partitioning of namespaces for debugging/tracing.

    The default length of 8 provides a 0.2% chance of collision in 1M instances
    as per the birthday paradox; make longer if this is a risk.

    Debug mode supports easily readable keys. The 4 random length of the key
    means a 1% collision chance at 500; since debug is only for low-volume
    testing, this should be acceptable.
    """
    if settings.DEBUG:
        prefix += 'D'
        token = get_random_string( 4 ).lower()
    else:
        token = get_random_string( length )

    return prefix + token + suffix
