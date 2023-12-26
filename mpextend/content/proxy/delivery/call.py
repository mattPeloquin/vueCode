#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Calls to external endpoints made from here with requests library
"""
import re
import requests
from django.core.cache import caches
from django.template.response import TemplateResponse

from mpframework.common import log
from mpframework.common.api import respond_api
from mpframework.common.utils import join_urls
from mpframework.content.mpcontent.delivery import parse_session_path

from . import full_url
from .request import request_options
from .response import fixup_response


_cache = caches['default']


def get_proxy_response( request, orig_url, options ):
    """
    Call external endpoint from a protected access session request,
    fixup the response based on configuration options.
    Returns a Django HttpResponse with proxy return or error.

    The call may be the original protected request, or subsequent
    requests in the response that use relative pathing. The original request
    may be to a host or specific link, which are managed differently
    during replacement.
    """
    rv = None

    # Note request will be going outside system, so can't control response time
    request.is_proxy = True
    request.mpinfo['response_type'] = 'proxy'

    # The original url must include host (with or without subdomain), and may
    # also include a path specific resource (and query strings)
    orig_host = _host( orig_url )

    # Take steps to preserve trailing slash on path request
    orig_path = request.path
    append_slash = orig_path.endswith(('/', '\\'))

    # 'path' is used for any part of the request url that is after
    # the protected access session portion of the url
    _session, path = parse_session_path( orig_path )

    try:
        # Determine whether the original url should be called as-is, or if
        # this is a subsequent call to the proxy that fixed up.
        if not path:
            # For original call, add optional home path; used if proxy URL
            # needs paths that are not under the home path
            url = join_urls( orig_url, options.get( 'home', '' ) )
        else:
            # For subsequent calls from the home page, build full path
            url = full_url( request, orig_host, path, append_slash=append_slash )

        # Any other adjustments to url
        force_http = options.get('force_http')
        if force_http and url.startswith('https'):
            url = url.replace( 'https', 'http', 1 )

        # See if the url is eligible for shared caching
        shared_caching = False
        cache_share = options.get('response_cache_share')
        if cache_share:
            path_match = re.compile( cache_share['url_regex'],
                                        re.VERBOSE | re.IGNORECASE )
            if path_match.search( path ):
                shared_caching = True

        rv = _get_response( request, url, options, orig_host, shared_caching )

    except Exception:
        log.exception("PROXY ERROR %s, %s: %s", request.mptiming,
                        request.mpipname, request.uri)
    if not rv:
        if request.is_api:
            rv = respond_api( error=u"Could not reach external service" )
        else:
            rv = TemplateResponse( request, 'proxy/proxy_failure.html', {} )
    return rv

def _get_response( request, url, options, orig_host, shared_caching ):
    """
    Make the request to external URL using 'requests' library and
    call fixup_response to get fixed up Django response object.
    """
    response = None
    roptions = request_options( request, options )

    # Check the cache if caching configured for this url
    cache_key = None
    if shared_caching:
        cache_key = _shared_cache_key( request, url, roptions, options )
        if cache_key:
            response = _cache.get( cache_key )
    if response:
        log.info2("PROXY CACHE: %s -> %s", request.mpipname, cache_key)

    # If no cache call the external server
    else:
        if log.info_on() > 1:
            rt = request.mptiming
            log.debug("PROXY CALL %s, %s: %s %s %s c%s", rt, request.mpipname,
                        request.method, url, str(roptions), str(cache_key))
            rt.mark()
        try:
            response = requests.request( request.method, url, **roptions )

            log.debug("PROXY RETURN %s, %s: %s %s", request.mptiming, request.mpipname,
                        response, url)

            response = fixup_response( request, response, options, orig_host )

            # Cache the Django HttpResponse
            # Proxy responses should only be cached if there will be NO changes
            # in response from any header information sent to the external server
            if cache_key and response and response.status_code in [ 200 ]:
                _cache.set( cache_key, response )

            if log.info_on() > 1:
                log.info2("PROXY(%s) %s -> %s %s %s", rt.log_recent(), request.mpipname,
                            response and response.status_code, url,
                            str( roptions.get( 'params', '' ) ) )

        except requests.ReadTimeout:
            log.warning("PROXY TIMEOUT %s, %s: %s", request.mptiming,
                        request.mpipname, request.uri)
            if request.is_api:
                msg = u"Server did not respond in {} seconds.".format(
                            roptions.get('timeout') )
                response = respond_api( error=msg )
            else:
                response = TemplateResponse( request, 'proxy/proxy_timeout.html', {
                                'timeout': roptions.get('timeout') })
    return response

def _shared_cache_key( request, url, roptions, options ):
    """
    Used for responses from proxy that can be safely cached depending on options.

    Any shared file caching MUST rely on file name versioning for invalidation.
    """
    # Do not cache posts or files
    if roptions.get('data') or roptions.get('files'):
        return

    # Create subset of unique cache items
    cache_options = {
        'query_string': roptions.get( 'params', '' ),
        'auth': roptions.get( 'auth', '' ),
        'request_headers': options.get('request_headers'),
        }

    # Optional cache items
    if options.get('cache_user'):
        cache_options['user'] = request.user.pk

    return "PROXY_s{}_{}_{}".format( request.sandbox.pk, url, cache_options )

def _host( url ):
    # Returns url path without scheme, if exists
    if url.startswith('http'):
        segments = url.split('//')
        return segments[1]
    else:
        return ''
