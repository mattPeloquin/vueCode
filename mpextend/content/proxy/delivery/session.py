#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Session management for proxy calls

    Interaction with a proxy often requires multiple calls, so the proxy session
    uses MPF cache to save state.
"""

from mpframework.common.utils import now
from mpframework.common.utils import get_random_key
from mpframework.common.utils import timedelta_seconds


def proxy_access_session( access_session, session_type ):
    """
    Return new session for proxy handler to use when there are calls from
    the proxied iframe launched from the original proxy request.
    Browsers may not like reusing access URL, so setup as new session and
    access url vs. building on the original one.
    """
    rv = access_session.copy()

    # Track whether initial call to proxy source was made
    rv['initial'] = True
    rv['initial_key'] = access_session['key']

    # Values for the access session
    rv['access_type'] = session_type
    rv['key'] = get_random_key( prefix='p' )
    rv['url'] = access_session['url'].replace( access_session['key'], rv['key'] )

    # Adjust new timeout to be relative to start
    delta = timedelta_seconds( now() - access_session['start'] )
    rv['timeout'] = access_session['timeout'] - delta

    return rv
