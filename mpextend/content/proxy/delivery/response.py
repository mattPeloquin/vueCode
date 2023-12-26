#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Fixup responses from proxy source
"""
import re
from django.http import HttpResponse
from django.urls import reverse

from mpframework.common import log
from mpframework.common.utils import join_urls
from mpframework.content.mpcontent.delivery import parse_session_path

from . import full_url
from .headers import custom_headers


REGEX_PREFIX = '__re__'


def default_fixups():
    """
    These fixups are applied when no fixups are defined
    """
    return {
        'default': {
            'path_regex': '.*',
            'replacements': {
                'replace_host': '{session_url}',
                REGEX_PREFIX + r'([=\(])(["\'])/(?![/])': r'\1\2/{session_url}/',
                }
            }
        }

def host_url( request, *path ):
    """
    Returns URL to access proxy URL through the platform
    """
    return full_url( request, request.host, *path ).strip('/')

def fixup_response( request, response, options, orig_host ):
    """
    Each response from proxy is run through here to modify the returned
    HTML with path and other fixups.
    Returns a Django HttpResponse object or None.
    """
    if response is None:
        return
    log.debug("Proxy response headers: %s", response.headers)
    log.debug("Proxy response content: %s", response.content[:1024])
    include_headers = options.get('headers', [])

    # Don't fixup downloads, and include all headers
    if response.headers.get('content-disposition'):
        fixup_text = False
        include_all_headers = True

    # Otherwise fixup response body
    else:
        fixup_text = _fixup_response_text( request, response, options, orig_host )
        include_all_headers = options.get('all_headers')

    # Create Django response from proxy response
    rv = HttpResponse( fixup_text or response.content,
                       status=response.status_code,
                       content_type=response.headers.get( 'content-type', '' ) )

    # Bring over proxy response headers based on options
    for key, value in response.headers.items():
        if include_all_headers or key.lower() in include_headers:
            rv[ key ] = value

    # Add any custom response headers
    headers = custom_headers( request, options.get('response_headers') )
    if headers:
        log.debug("Proxy response header update: %s", headers)
        for key, value in headers.items():
            rv[ key ] = value

    return rv

def _fixup_response_text( request, response, options, orig_host ):
    """
    Perform any text fixups on the response
    """
    rv = None
    for name, fixup in options.get( 'response_text_replace', {} ).items():
        log.debug2("Proxy response fixup: %s -> %s", name, fixup)
        try:
            path_match = re.compile( fixup['path_regex'],
                                        re.VERBOSE | re.IGNORECASE )
            # Apply ONE FIXUP to the FIRST path match
            if path_match.search( request.path ):

                # Long response strings with unicode can take seconds
                # to convert response to text. Provide option to override
                # with explicit encoding if this is a problem
                encoding = fixup.get('encoding')
                if encoding:
                    response.encoding = encoding

                rv = _response_replacements( request, response.text,
                                    fixup['replacements'], options, orig_host )

                break
        except Exception as e:
            log.info("CONFIG - Proxy fixup exception %s: %s -> %s, %s",
                            request.mpipname, e, name, fixup)
    return rv

def _response_replacements( request, html, replacements, options, orig_host ):
    """
    Replace any original host references and call custom replacements
    """
    if replacements:
        try:
            for match, replacement in replacements.items():

                # Replace host with MPF request host
                if 'replace_host' == match:
                    match = orig_host

                # Do any custom replacements
                try:
                    html = _response_replacement( request, html, options,
                                                    match, replacement )
                except Exception as e:
                    log.info("CONFIG - Proxy rule bad: %s: %s -> %s, %s",
                                    request.mpipname, e, match, replacement)
        except Exception as e:
            log.info("CONFIG - Proxy replacement bad %s: %s -> %s",
                            request.mpipname, e, replacements)
    return html

def _host_cache( cache_id ):
    proxy_url = reverse( 'protected_proxy_cache', kwargs={ 'cache_id': cache_id } )
    return join_urls( '{{host_root}}/{}'.format( proxy_url ) )

def _response_replacement( request, html, options, match, replacement ):
    """
    Implement custom replacements and well-known tags
    """
    session, path = parse_session_path( request.path )

    # General replacement tags
    for m in re.finditer( _tag_match, replacement ):
        tag = m.group(1)
        value = options['tags'][ tag ]
        tag_replacement = {}
        tag_replacement[ 'tag_{}'.format( tag ) ] = value
        replacement = replacement.format( **tag_replacement )

    # Tag for adding url for caching
    if '{host_cache}' in replacement:
        replacement = replacement.format( host_cache=_host_cache(
                                            options['host_cache_id'] ) )

    # Root request path
    if '{host_root}' in replacement:
        replacement = replacement.format( host_root=host_url( request ) )
    # Full request path
    elif '{host_proxy}' in replacement:
        replacement = replacement.format(
                        host_proxy=host_url( request, request.path ) )
    # Protected path with session id
    elif '{session_url}' in replacement:
        replacement = replacement.format( session_url=session )
    # Protected path after session
    elif '{path_url}' in replacement:
        replacement = replacement.format( path_url=path )

    # Do swap with regex or straight replace
    if match.startswith( REGEX_PREFIX ):
        match = match.replace( REGEX_PREFIX, '' )
        match_re = re.compile( match )
        new_html = re.sub( match_re, replacement, html )
    else:
        new_html = html.replace( match, replacement )

    if log.debug_on() and not html == new_html:
        log.debug("PROXY REPLACE %s, %s: %s -> %s", request.mptiming,
                    request.uri, match, replacement )
    return new_html

_tag_match = re.compile( r'{tag_(.+)}', re.IGNORECASE )
