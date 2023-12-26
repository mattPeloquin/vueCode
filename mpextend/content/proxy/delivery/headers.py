#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Support for adding custom headers
"""
import re
from django.conf import settings

from mpframework.common import log
from mpframework.common.utils import json_dump
from mpextend.product.account.utils import get_ga


def custom_headers( request, headers ):
    """
    Return dict with copy of all headers with any tags replaced,
    used for both request and response headers
    """
    rv = {}
    if headers and isinstance( headers, dict ):
        for key, value in headers.items():
            try:
                _header_item( key, value, request, rv )
            except Exception as e:
                if settings.MP_DEV_EXCEPTION:
                    raise
                log.info("CONFIG - Proxy header: %s -> %s", request.mpipname, e)
    return rv

def _header_item( key, value, request, rv ):

    # Path-specific headers
    if isinstance( value, dict ):
        path_match = re.compile( value['path_regex'], re.VERBOSE | re.IGNORECASE )
        if path_match.search( request.path ):
            rv[ value['key'] ] = _update_value( value['value'], request )

    # Key-value pairs added to every header
    else:
        rv[ key ] = _update_value( value, request )

def _update_value( value, request ):
    user = request.user

    # Add any MPF tags
    # Requests/httplib can't handle unicode strings in headers, so encode
    if '{info}' == value:
        value = str( _get_info( request ) ).encode( 'utf-8', 'replace' )
    elif '{user_id}' == value:
        value = str( user.pk )
    elif '{email}' == value:
        value = str( user.email ).encode( 'utf-8', 'replace' )
    elif '{name}' == value:
        value = str( user.name ).encode( 'utf-8', 'replace' )
    elif '{sandbox}' == value:
        value = str( user.sandbox.subdomain ).encode( 'utf-8', 'replace' )

    return value

def _get_info( request ):
    """
    Put detailed, optional info into a JSON string in header
    """
    rv = {}
    user = request.user
    rv['user'] = {
            'id': user.pk,
            'email': user.email,
            'name': user.name,
            'staff': user.staff_level,
            'workflow': user.workflow_level,
            'image': user.image_url,
            'group': user.external_group,
            }

    ga = get_ga( user )
    if ga:
        rv['account'] = {
            'id': ga.pk,
            'name': ga.base_account.name,
            'image': ga.image_url,
            'group': ga.external_group,
            }

    return json_dump( rv )
