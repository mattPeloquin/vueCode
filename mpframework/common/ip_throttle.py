#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Utilities for IP throttling and banning

    FUTURE -- Add banned IP in AWS WAF for big attacks
"""
from django.conf import settings
from django.core.cache import caches

from mpframework.common import sys_options


THROTTLE = settings.MP_TUNING['THROTTLE']

# Sanity check on maximum banned IPs to show in UI
MAX_IPS = 1000

# Integer count marker used to identify IPs over threshold
BANNED_MARKER = 666666666

# Request cache is optimized for per-request info
_cache = caches['request']

# Use local small cache for ban optimization since it supports expiration
_local = caches['local_small']


def _throttle_key( ip ):
    return f'ipthrt_{ ip }'

def _count_key( ip ):
    return f'ipbans_{ ip }'

def check_ip_limiting( ip ):
    """
    Manage IP throttling and banning
    Returns an error description if IP should not be allowed access.
    Local cache is used for performance, so sensitivity will be
    heavily influenced by whether stick sessions are on.
    """
    if settings.MP_TESTING:
        return

    # Get the current threshold; 0 turns off checking
    threshold = sys_options.throttle_thresh()
    if not threshold:
        return

    tkey = _throttle_key( ip )

    # Check for local buffer ban, bail immediately
    if _local.get( tkey ):
        return "BANNED IP - LOCAL"

    requests = _cache.get( tkey )

    # Add throttle counter if it doesn't exist, allow through
    if not requests:
        _cache.set( tkey, 1, sys_options.throttle_period() )

    # If IP banned in distributed cache, skip and bump local
    elif requests >= BANNED_MARKER:
        _local.set( tkey, 1, THROTTLE['LOCAL_SECONDS'] )
        return "BANNED IP"

    # Throttle IP if too many requests
    elif requests > threshold:
        if ip not in sys_options.throttle_exempt():
            full = ban_ip( ip )
            return "BANNING IP - FULL" if full else "BANNING IP - WARN"

    # Otherwise do increment on request and allow through
    else:
        try:
            _cache.incr( tkey )
        except ValueError:
            pass

def ban_ip( ip, seconds=None ):
    """
    Ban throttle by boosting the throttle count over the 'banned' amount.
    Returns None if warning ban is used, True for full ban, or seconds if
    an explicit ban was requested.
    """
    count = _cache.get( _count_key( ip ) ) or { 'ip': ip }
    count['throttles'] = count.get('throttles', 0) + 1
    _cache.set( _count_key( ip ), count, THROTTLE['BAN_AGE'] )
    rv = seconds
    if not seconds:
        if count['throttles'] > sys_options.ban_threshold():
            seconds = sys_options.ban_seconds()
            rv = True
        else:
            seconds = sys_options.warn_seconds()
    _cache.set( _throttle_key( ip ), BANNED_MARKER, seconds )
    return rv

def boost_ip( ip, mult=1 ):
    """
    Add hits to the threshold counter for more expensive endpoints.
    """
    if settings.MP_TESTING or not sys_options.throttle_thresh():
        # Don't go forward if no throttle key would have been created
        return
    boost = mult * sys_options.throttle_thresh_boost()
    _cache.incr( _throttle_key( ip ), boost )

def banned_ips():
    """
    Potentially expensive search in cache only intended
    for use in root admin console.
    """
    search = '*{}*'.format( BANNED_MARKER )
    keys = [ k for k in _cache.iter_keys( search, MAX_IPS ) ]
    return _cache.get_many( keys )
