#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Time window cache support

    Timewins are cache groups that use version cache to store the start of
    time windows, which split between a long-term base that doesn't
    change, and more recent deltas that can be merged.
"""
from hashlib import sha1

from ..utils import now
from ..utils import get_random_key
from .version import cache_version


def get_timewin_start( version_key ):
    """
    Return active timewin start datetime, or none
    """
    return timewin_start( version_key, None )

def get_timewin_hash( version_key ):
    """
    Return unique hash string for a timewin start date.
    If no timewin is set yet, return a random string, which will
    prevent any caching based on the hash.
    """
    start = get_timewin_start( version_key )
    if not start:
        return get_random_key()
    # sha1 hexdigest is 40 chars long, just grab start
    digest = sha1( str(start).encode( 'utf-8', 'replace' ) ).hexdigest()
    return digest[:8]

def timewin_start( version_key, length ):
    """
    Sets up timewin end dates for timewin groups by get/create of version
    with embedded date.
    """
    # If key with timewin data already exists, provide it
    time_start = cache_version( version_key, version_fn=lambda: False )
    if time_start:
        return time_start
    # Otherwise set new time window
    if length:
        return cache_version( version_key, version_fn=lambda: now(),
                                force_set=True, timeout=length )
