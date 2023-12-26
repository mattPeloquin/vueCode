#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Utility URLs for specific purposes
"""

from django.conf import settings
from django.template.response import TemplateResponse


def edge_sandbox_css( request, _no_host_id, _cache_url=None ):
    """
    Provide sandbox css customizations as a link that can be loaded with a
    stylesheet link command and cached on the browser.
    Invalidation happens when the cache_url changes, triggering browser
    to call back here again.
    """
    response = TemplateResponse( request, '_base/style/sandbox.html.css', {} )
    response['content-type'] = 'text/css'
    response['cache-control'] = 'max-age={}'.format( settings.MP_CACHE_AGE['BROWSER'] )
    return response


def render_style_page( request, body_html ):
    """
    Renders the given HTML with the current sandbox style
    """
    return TemplateResponse( request, '_base/pages/style.html', {
                'body_html': body_html
                })
