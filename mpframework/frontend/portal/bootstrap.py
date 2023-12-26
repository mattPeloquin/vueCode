#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Portal bootstrap - facades for portal data
    Supports both API and embedded JSON data for inflating the portal.
    API calls are public - if a bootstrap fn lacks needed authentication
    an empty set is returned.

    Apps add data to bootstrap with mpf_function_group_register, which
    adds a function that returns data which will be converted to JSON.
    The bootstrap groups represent sets of data cached in the same manner,
    which can be placed in API calls or embedded in the page loading.

    There are 4 ways to access bootstrap data, driven by performance relative
    to pattern of cache invalidation:

        - Embed in page request, no caching
        - Browser and Cloudfront cached URL
        - Direct cached URL
        - Direct uncached URL

    Each of these can make use of a mix of time window and group caching.
    The goal is to get as much critical data to portal as fast as possible
    to balance fast rendering with lazy loading and caching.
"""
from django.conf import settings

from mpframework import mpf_function_group_call
from mpframework.common import log
from mpframework.common.cache import cache_rv
from mpframework.user.mpuser.cache import user_timewin_get
from mpframework.user.mpuser.cache import user_timewin_start
from mpframework.content.mpcontent.cache import content_timewin_get
from mpframework.content.mpcontent.cache import cache_keyfn_content_timewin
from mpframework.content.mpcontent.cache import cache_keyfn_content


#--- Dict facades used for APIs or embed

def bootstrap_dict_embed( request ):
    rv = _bootstrap_dict( 'bootstrap_delta', request )
    rv.update( _content_notime( request ) )
    rv.update( _content_deltas( request ) )
    return rv

def bootstrap_dict_content_timewin( request ):
    return _content_timewin( request )

def bootstrap_dict_user_timewin( request ):
    return _user_timewin( request )

def bootstrap_dict_nocache( request ):
    rv = _bootstrap_dict( 'bootstrap_nocache', request )
    rv.update( _user_deltas( request ) )
    return rv

#--- Content data caching
# Most content uses time window and delta caching, but some does not
# The delta and notime caching uses content cache groups

@cache_rv( keyfn=cache_keyfn_content )
def _content_notime( request ):
    rv = _bootstrap_dict( 'bootstrap_content_notime', request )
    log.info2("CACHING content notime: %s -> %s ",
                request.mpipname, cache_keyfn_content(request))
    return rv

def _content_deltas( request ):
    """
    If timewin active, return deltas, otherwise start timewin and return all
    """
    delta_start = content_timewin_get( request )
    if delta_start:
        return _content_delta_values( request, delta_start )
    else:
        return _content_timewin( request )

@cache_rv( keyfn=cache_keyfn_content_timewin )
def _content_timewin( request ):
    # Get or setup timewin version date in call to cache version,
    # then get content
    rv = _bootstrap_dict( 'bootstrap_content_timewin', request )
    log.info2("CACHING content timewin: %s -> %s, %s -> %s", request.mpipname,
                len(rv['items']), content_timewin_get(request),
                cache_keyfn_content_timewin(request))
    return rv

@cache_rv( keyfn=lambda r, _: cache_keyfn_content(r) )
def _content_delta_values( request, delta_start ):
    # Cache the true deltas from an initialized time win
    # Send empty values for content so changes override the timewin data.
    rv = _bootstrap_dict( 'bootstrap_content_delta', request,
                            delta=delta_start )
    log.info2("CACHING content delta: %s -> %s, %s -> %s", request.mpipname,
                len(rv['items_delta']), delta_start,
                cache_keyfn_content(request))
    return rv

#--- User data caching
# User data caching uses a time window and no other caching

@cache_rv( keyfn=lambda _:( '', user_timewin_start ) )
def _user_timewin( request ):
    # Get or setup timewin version date in cache call, get user data if not cached
    return _bootstrap_dict( 'bootstrap_user_timewin', request )

def _user_deltas( request ):
    # Don't cache user deltas, as they are volatile
    delta_start = user_timewin_get( request )
    if delta_start:
        return _bootstrap_dict( 'bootstrap_user_delta', request,
                                last_used__gte=delta_start )
    else:
        return _user_timewin( request )

#-------------------------------

def _bootstrap_dict( bootstrap_group, request, **kwargs ):
    """
    Package results for a particular bootstrap group into dict
    """
    rv = {}
    bootstraps = mpf_function_group_call( bootstrap_group )
    for name, values_fn in bootstraps:
        log.debug("Adding to bootstrap: %s -> %s %s", name, values_fn, kwargs)
        try:
            raw_values = values_fn( request, **kwargs )

        except Exception:
            log.exception("Bootstrap values: %s", values_fn)
            if settings.MP_DEV_EXCEPTION:
                raise
            raw_values = []

        rv[ name ] = raw_values
    return rv
