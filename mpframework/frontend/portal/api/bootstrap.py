#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Portal bootstrap API calls

    For the API calls that cache timewin URLs on the browser/edge, provide a
    cache age equal to the timewin. This isn't strictly needed as the URLs
    requested on a page should change when timed out, and race conditions
    are handled by overlapping the windows. However it will reduce any
    risk of conflict related to long browser cache times. To make the URL
    match the timeout of the underlying timewin could calculate the seconds
    remaining at the time of the call, but that shouldn't be needed.
"""

from django.conf import settings

from mpframework.common import log
from mpframework.common.api import respond_api_call

from ..bootstrap import bootstrap_dict_content_timewin
from ..bootstrap import bootstrap_dict_user_timewin
from ..bootstrap import bootstrap_dict_nocache
from ..bootstrap import bootstrap_dict_embed

_content_age = settings.MP_CACHE_AGE['TIMEWIN_CONTENT']
_user_age = settings.MP_CACHE_AGE['TIMEWIN_USER']


def bootstrap_delta( request ):
    """
    Provide access to content usually embedded in page
    """
    log.debug("API Bootstrap embed: %s", request.user)
    def handler( _get ):
        return bootstrap_dict_embed( request )
    return respond_api_call( request, handler, methods=['GET'] )

def edge_bootstrap_content( request, no_host_id, cache_url=None ):
    """
    Core per-sandbox content JSON bootstrap
    Served through edge servers to share through edge caching
    """
    log.debug("API Bootstrap Content edge: %s, %s", request.sandbox, cache_url)
    def handler( _get ):
        return bootstrap_dict_content_timewin( request )
    return respond_api_call( request, handler, cache=_content_age, methods=['GET'] )

def bootstrap_user( request, cache_url=None ):
    """
    Core user data based on time window cache
    """
    log.debug("API Bootstrap User: %s, %s", request.user, cache_url)
    def handler( _get ):
        return bootstrap_dict_user_timewin( request )
    return respond_api_call( request, handler, cache=_user_age, methods=['GET'] )

def bootstrap_nocache( request ):
    """
    Register items that load slow and are not worth caching, cannot
    be easily cached, or contain the deltas for time window caching.
    """
    log.debug("API Bootstrap NoCache: %s", request.user)
    def handler( _get ):
        return bootstrap_dict_nocache( request )
    return respond_api_call( request, handler, methods=['GET'] )

def bootstrap_content( request, cache_url=None ):
    """
    Direct link for core content data based on time window cache
    """
    log.debug("API Bootstrap Content direct: %s, %s", request.sandbox, cache_url)
    def handler( _get ):
        return bootstrap_dict_content_timewin( request )
    return respond_api_call( request, handler, cache=_content_age, methods=['GET'] )

