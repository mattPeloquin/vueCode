#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    API utilities - all MPF endpoints assume:

        - JSON responses
        - HTTP codes reference API call outcome
        - No response envelope on success
        - Naked JSON arrays should never be returned
        - Standard error response on failure

    Public and authenticated endpoints are used and may be deployed
    into different url groups depending on performance/scaling needs.

    Calls are authenticated in the same manner as views; it is up to
    each response to ensure it honors tenancy restrictions on
    data and actions.

    The design of APIs varies - many endpoints are intended primarily
    for use by the MPF client, while others are intended for use
    by both MPF and external developer integrations.
    Endpoints intended for developer use are RESTish in nature, but in
    general the focus is on provide easy access to information vs.
    providing a rich REST experience.

    Because of history, MPF uses a mix of Fetch and XHR calls for endpoints,
    and the content type is always JSON.
"""
import json
from django.conf import settings
from django.http import Http404
from django.http import HttpResponse

from . import log
from .utils import json_dump
from .utils import safe_int


class mpApiArgsNullIdException( Exception ):
    """
    Raised when a null ID is passed, which can happen often if a bot is
    sniffing a public REST api
    """
    pass

def respond_api_expired( **kwargs ):
    response = kwargs
    response.update({ _API_EXPIRED_MARKER: True })
    return respond_api( response, error=True )
_API_EXPIRED_MARKER = '__mp_expired'

def respond_api( data=None, error=None, status=None, cache=False, **kwargs ):
    """
    Wrapper for handling response options API ajax requests.
    An HTTP error is returned when:
     - values is False - use None for empty success
     - error is truthy
    """
    expired = False
    if not error:
        if data is False:
            error = u"The request failed"
        if data and getattr( data, _API_EXPIRED_MARKER, False ):
            expired = True
            error = u"The request has expired"

    if error:
        response = { 'error': error, 'expired': expired }
    else:
        response = data if data else {}
    response = json_dump( response )

    if status is None:
        status = 404 if error else 200

    response = HttpResponse( response, status=status,
                content_type='application/json', **kwargs )

    if cache:
        age = settings.MP_CACHE_AGE['BROWSER'] if cache is True else cache
        response['cache-control'] = 'max-age={}'.format( age )

    log.debug_values("respond_api: %s", response)
    return response

def respond_api_call( request, handler_or_payload=None, cache=False, methods=None ):
    """
    MPF supports GET, POST, PUT, and PATCH for API calls.
    (PUT and PATCH based on compatibility settings, due to firewall problems)
    """
    request.mpinfo['response_type'] = 'api'

    # handler_or_payload provides JSON response, which may be a function that
    # is called, an object to send, or a null value.
    if hasattr( handler_or_payload, '__call__' ):
        handler = handler_or_payload
    else:
        def _value_handler( *args ):
            return handler_or_payload
        handler = _value_handler

    values = {}
    error = u"We've experienced a network problem"
    try:
        # Support limiting HTTP call methods
        methods = methods or ['GET', 'POST', 'PUT', 'PATCH']
        if request.method not in methods:
            log.info("SUSPECT API - %s bad method: %s -> %s",
                            handler.__name__, request.mpipname, request.method)
        else:
            # Call the API handler
            values = _get_values( request, handler )
            error = False

    except Http404:
        log.info2("API 404: %s -> %s", request.mpipname, request.uri)
    except mpApiArgsNullIdException as e:
        log.info("SUSPECT API: %s, %s -> %s", e, request.mpipname, request.uri)

    return respond_api( values, error=error, cache=cache )

def _get_values( request, handler ):
    """
    Return values from API handler based on method type
    """
    rv = {}

    if 'GET' == request.method:
        log.debug2("API GET: %s -> %s", handler.__code__, request.GET)
        rv = handler( request.GET )

    elif 'POST' == request.method:
        # Handle optional JSON encoding of dict
        payload = request.POST.dict()
        if payload.get('json_data'):
            payload = json.loads( payload.get('json_data') )
        # Add file info for file posts
        if( request.FILES ):
            payload['post_FILES'] = {
                name: file.name for name, file in request.FILES.items()
                }
        log.debug2("API POST: %s -> %s", handler.__code__, payload)
        rv = handler( payload )

    elif 'PUT' == request.method or 'PATCH' == request.method:
        json_values = request.read()
        log.debug2("API %s: %s -> %s", request.method, handler.__code__, json_values)
        rv = handler( json.loads( json_values ) )

    return rv

def api_get_id( id, required=True ):
    """
    Standardized test to get non-zero integer id out of an API request.
    """
    rv = safe_int( id )
    if not rv is None or rv == 0:
        try:
            rv = id.get('id')
        except Exception:
            rv = getattr( id, 'id', None )
        rv = safe_int( id )
    if required and not rv:
        raise mpApiArgsNullIdException("Null ID in object")
    return rv
