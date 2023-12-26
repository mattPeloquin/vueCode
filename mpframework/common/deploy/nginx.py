#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    NGINX specific code
"""
from django.conf import settings
from django.http import HttpResponse

from ..utils.http import join_urls
from ..utils.http import attachment_string


def accel_redirect( location, path, status=200, attachment=None, cache=False ):
    """
    Return NGINX accel-redirect
    """
    path = join_urls( location, path )

    response = HttpResponse( status=status )
    response['X-Accel-Redirect']    = path
    response['content-type']        = ''   # Force nginx to determine type
    response['content-disposition'] = attachment_string( attachment )

    if cache:
        response['cache-control'] = 'max-age={}'.format(
                    settings.MP_CACHE_AGE['BROWSER'] )
    return response


def accel_redirect_protected( path, attachment=None ):
    """
    Protected accel redirects assume a relative path is provided
    """
    return accel_redirect( settings.MP_URL_PROTECTED_XACCEL,
                join_urls( settings.MP_AWS_S3_PROTECTED_ENDPOINT, path ),
                attachment=attachment )

def accel_redirect_public( path ):
    """
    Public accel redirects may use relative or absolute path. Since the
    path may be public, force http since current server configuration
    was not able to resolve https x-accel requests through cloudfront
    even though they can wget them.
    """
    if settings.MP_CLOUD:
        if not path.startswith('http'):
            path = join_urls( settings.MP_AWS_S3_PUBLIC_ENDPOINT, path )
    path = path.replace('https', 'http')
    return accel_redirect( settings.MP_URL_PUBLIC_XACCEL, path, cache=True )
