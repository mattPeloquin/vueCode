#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Content cache support

    Preparing content for client presentation is a major driver of load,
    so is optimized with URLs cached in browser.
    Content may be edited frequently, so simplistic invalidation of all provider
    caching on content changes was not ideal. The timewin approach allows most
    content changes to be handled in a recent time window. All content is
    cached at a point in time with browser URL, and then only the deltas are
    sent to the client, until the window times out.
    Invalidation also considers provider vs. isolate sandboxes scope
    and workflow (dev items shouldn't be sent to non-staff).
"""
from django.conf import settings

from mpframework.common.cache.groups import cache_group_sandbox
from mpframework.common.cache.groups import cache_group_provider
from mpframework.common.cache.groups import invalidate_group_sandbox
from mpframework.common.cache.groups import invalidate_group_provider
from mpframework.common.cache.timewin import timewin_start
from mpframework.common.cache.timewin import get_timewin_start
from mpframework.common.cache.timewin import get_timewin_hash


_timewin_timeout = settings.MP_CACHE_AGE['TIMEWIN_CONTENT']


def cache_keyfn_content_timewin( request ):
    return _content_key( request ), content_timewin_start( request )

def cache_keyfn_content( request ):
    return _content_key( request ), cache_group_content_sandbox( request.sandbox )

"""
    Non-timewin and delta content cache_group version_key is based on scope
    of EITHER entire provider or isolated sandboxes based on the isolate
    sandbox setting.
    When a provider is set to isolate_sandboxes, caching and invalidation of
    content takes place ONLY with sandbox ID, so if there happens to be content
    shared between the sandboxes it will not be invalidated correctly.

    The 'cnt' namespace is used, and there is no upstream groups for
    content -- so content caching CANNOT HAVE DEPENDENCIES ON OPTIONS.
"""

def cache_group_content( provider_id=None, sandbox_id=None ):
    if sandbox_id:
        return cache_group_sandbox( sandbox_id, namespace='cnt' )
    else:
        assert provider_id
        return cache_group_provider( provider_id, namespace='cnt' )

def invalidate_group_content( provider_id, sandbox_id ):
    # If a sandbox ID is provided, isolated sandbox is assumed
    if sandbox_id:
        invalidate_group_sandbox( sandbox_id, namespace='cnt' )
    else:
        invalidate_group_provider( provider_id, namespace='cnt' )

def cache_group_content_sandbox( sandbox ):
    if sandbox.provider.isolate_sandboxes:
        return cache_group_content( sandbox_id=sandbox.pk )
    else:
        return cache_group_content( provider_id=sandbox._provider_id )

"""
    Timewin groups can be invalidated either with sandbox ids, or
    across a provider's tenant group. The default provider group is used
    instead of 'cnt', since that is invalidated with every content change.
"""

def content_timewin_start( request ):
    """
    Sets up timewin start datetime and return the version group for
    retrieving the datetime.
    """
    group = content_timewin_version( request )
    timewin_start( group, _timewin_timeout )
    return group

def content_timewin_version( request ):
    """
    Timewin version key includes separate sandbox and provider keys because
    different invalidation scenarios have only one or other.
    """
    sandbox = request.sandbox
    tw_group = content_timewin_group_sandbox( sandbox.pk )
    provider_group = content_timewin_group_provider( sandbox._provider_id )
    return tw_group + '-' + provider_group

def content_timewin_group_sandbox( sandbox_id ):
    return cache_group_sandbox( sandbox_id, namespace='twcnt' )
def content_timewin_group_provider( provider_id ):
    return cache_group_provider( provider_id, namespace='twcnt' )

def invalidate_group_content_timewin_sandbox( sandbox_id ):
    invalidate_group_sandbox( sandbox_id, namespace='twcnt' )
def invalidate_group_content_timewin_provider( provider_id ):
    invalidate_group_provider( provider_id, namespace='twcnt' )

def content_timewin_get( request ):
    return get_timewin_start( content_timewin_version( request ) )

def content_timewin_hash( request ):
    return get_timewin_hash( content_timewin_version( request ) )


def _content_key( request ):
    """
    Returns cache key for a request's content.
    The default (all content) returns a blank key, while requests targeted at
    specific content (where the content is both defined with the request and
    set to embed that specific content in the page) return the content's key.
    """
    rv = ''
    content = request.mpstash.get('request_content')
    if content and request.sandbox.options['bootstrap.content_data_in_page']:
        rv = content.unique_key
    return rv
