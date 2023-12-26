#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Logic for request to proxy server
"""
from django.conf import settings

from mpframework.common import log

from .headers import custom_headers


def request_options( request, options ):
    """
    Setup requests options for proxy call
    """
    rv = {
        'timeout': min(
            float( options.get( 'timeout',
                        settings.MP_PROXY.get( 'DEFAULT_TIMEOUT', 1.0 ) ) ),
            float( settings.MP_PROXY.get( 'MAX_TIMEOUT', 10.0 ) )
            ),
        }

    # Always check for query params, as they are valid on non-Get requests
    rv.update({ 'params': request.GET.dict() })

    # Post data needs to handle duplicate keys and transform from the
    # Django data representation to requests
    if 'POST' == request.method:
        data = {}
        for key, values in request.POST.lists():
            data[ key ] = values
        rv.update({ 'data': data })

    if request.FILES:
        rv.update({ 'files': request.FILES })

    # Add any basic auth credentials
    credentials = options.get('credentials')
    if credentials:
        rv.update({ 'auth': (
            credentials['user'],
            credentials['password'],
            ) })

    # Add request header values that send default and/or custom information
    # to the proxy using available user information
    headers = {}
    if not options.get('suppress_default_request_headers'):
        headers.update( _default_headers( request ) )
    headers.update( custom_headers( request, options.get('request_headers') ) )
    if headers:
        rv.update({ 'headers': headers })

    log.debug2("Proxy request options: %s -> %s", request.uri, rv)
    return rv

def _default_headers( request ):
    """
    Set of headers sent by default with each request
    """
    return custom_headers( request, {
            'VUE-ID': '{user_id}',
            'VUE-NAME': '{name}',
            'VUE-EMAIL': '{email}',
            'VUE-SITE': '{sandbox}',
            'VUE-INFO': '{info}',
            })
