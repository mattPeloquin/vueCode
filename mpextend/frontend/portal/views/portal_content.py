#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Portal content endpoints limit portal to specific content.

    HTTP responses for portal content page requests, which show subsets
    of portal content for stand-alone or iframe.
"""

from mpframework.common import log
from mpframework.foundation.ops.csp import iframe_allow_any
from mpframework.content.mpcontent.utils import content_search

from ._extra import process_extra
from .portal import sandbox_portal_extend


@iframe_allow_any
def portal_content( request, **kwargs ):
    request.is_portal_content = True
    _set_content( request, kwargs )
    return sandbox_portal_extend( request, **kwargs )

def portal_content_extra( request, **kwargs ):
    process_extra( request, kwargs )
    return portal_content( request, **kwargs )


def _set_content( request, kwargs ):
    context = kwargs.get( 'context', {} )
    # Determine item id for the requested content and
    # Setup downstream request and context settings
    content_slug = kwargs.pop('content_slug')
    content = content_search( request, content_slug )
    if content:
        log.debug("portal_content: %s", content)

        request.mpstash['request_content'] = content

        if content.is_collection:
            portal_content = 'collection'
            request.skin.frame_type = 'C'
        else:
            portal_content = 'item'
            request.skin.frame_type = 'I'

        request.mpstash['portal_content'] = portal_content
        context['portal_content'] = portal_content

        # Setup open graph meta data
        context['meta'] = {
            'title': content.name,
            'description': content.description,
            'image': content.image1,
            }

        # HACK - pass info on which url was used
        url_name = 'portal_content'
        if 'theme_id' in kwargs:
            url_name = 'portal_content_theme'
        elif 'frame_id' in kwargs:
            url_name = 'portal_content_frame'

        context['url_portal_args'] = {
            # Setup URL to stick on content instead of reverting to main site
            'url_name': url_name,
            'url_kwargs': { 'content_slug': content_slug },
            }

    kwargs['context'] = context
