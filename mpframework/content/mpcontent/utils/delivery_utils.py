#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared support code for delivery functionality
"""
from django.conf import settings

from mpframework.common import log
from mpframework.common.aws.cloudfront import get_signed_url
from mpframework.common.aws.cloudfront import get_signed_cookies
from mpframework.common.utils import join_urls
from mpframework.common.delivery import *


def parse_key_path( key_path ):
    """
    Parse session key from path and try to retrieve
    """
    key_path_seg = key_path.strip('/').split('/')
    key = key_path_seg[1]
    return key, key_path_seg[2:]

def parse_session_path( key_path ):
    """
    Parse session key from path
    The convention is any protected access URL will have protected url prefix
    in the path segment followed by the session id.
    """
    key_path_seg = key_path.strip('/').split('/')
    for pos, seg in enumerate( key_path_seg ):
        if seg.startswith( settings.MP_URL_PROTECTED ):
            pos += 2 # One for zero index, one to capture session
            session = key_path_seg[:pos]
            path = key_path_seg[pos:]
            return join_urls( *session ), join_urls( *path )

def download_path( session_path, key_path, file_path ):
    """
    Given list of keypath segments, make path with them appended to
    the access session data path segments.
    File downloads will store the base path in the access session; the primary
    download will be stored in the session, but any further relative paths
    will be appended to the path stored in the session.
    """
    base_path = join_urls( *session_path )
    key_path_end = len( session_path )
    end_path = join_urls( *key_path[ key_path_end: ]
                          ) if len(key_path) > key_path_end else file_path
    return join_urls( base_path, end_path )

def cf_signed( request, access_session, path=None ):
    """
    Returns true if the content should be redirected to Cloudfront
    """
    if not settings.MP_CLOUD:
        log.debug("SKIPPING Cloudfront delivery: %s -> %s", access_session, path)
        return False

    rv = use_signed( access_session['delivery_mode'], path )

    log.debug("Protected CF delivery: %s -> %s, %s", rv, request.sandbox, path)
    return rv

def cf_url( access_session, url ):
    """
    Get the base URL for access of the content through cloudfront
    with an adjustment for compatibility CF url.
    """
    cfdist = settings.MP_ROOT_URLS['URL_EDGE_PROTECTED']
    if access_session['compat_urls']:
        cfdist = settings.MP_ROOT_URLS['URL_EDGE_PROTECTED_COMP']
    rv = join_urls( cfdist, url, scheme=True, quote=True )
    log.debug2("CF url: %s", rv)
    return rv

def cf_querystring_url( access_session, url ):
    """
    Add CF signed query strings to url
    """
    ip = cf_ip( access_session )
    timeout = access_session['timeout']
    url = cf_url( access_session, url )
    rv = get_signed_url( url, timeout, ip )
    log.debug2("CF querystring: %s", rv)
    return rv

def cf_add_cookies_response( access_session, response ):
    """
    Add CF signed cookies to response
    """
    ip = cf_ip( access_session )
    timeout = access_session['timeout']
    cookies = get_signed_cookies( response.url, timeout, ip )
    for key, value in cookies.items():
        log.debug2("CF cookie: %s -> %s", key, value)
        response.set_cookie( key, value, httponly=True, secure=True,
                    samesite=cf_samesite( access_session ) )

def cf_ip( access_session ):
    """
    Should IP be included in Cloudfront signing?
    In some some user networks, IP can change within sessions, which will mess
    up Cloudfront signing to URL for content like LMS packages that are
    serving multiple files from the same url/cookie.
    """
    mode = access_session['delivery_mode']
    use_ip = mode.startswith( DELIVERY_PROT )
    return access_session['ip'] if use_ip else None

def cf_open_url( *args ):
    """
    CF link to the unprotected S3 folders
    """
    return join_urls( settings.MP_ROOT_URLS['URL_EDGE_PROTECTED_PUBLIC'],
                *args, scheme=True )

def cf_samesite( access_session ):
    return 'none' if access_session['compat_urls'] else 'strict'
