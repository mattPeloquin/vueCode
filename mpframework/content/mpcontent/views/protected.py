#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Views for default protected content access using delivery.py
"""
from django.conf import settings
from django.http import Http404
from django.http import HttpResponsePermanentRedirect
from django.views.decorators.csrf import csrf_exempt

from mpframework.common import log
from mpframework.common.aws.s3 import url_add_attachment
from mpframework.common.deploy.nginx import accel_redirect_protected
from mpframework.common.utils import join_urls
from mpframework.common.utils.http import attachment_string
from mpframework.common.utils.http import append_querystring
from mpframework.foundation.ops.csp import iframe_allow_any

from ..delivery import set_access_request_handler
from ..delivery import set_access_response_handler
from ..delivery import protected_access_url_response
from ..delivery import protected_access_cookie_response
from ..utils.delivery_utils import *


@csrf_exempt
@iframe_allow_any
def url_access( request ):
    """
    Responds to request directly with content, or provides a URL that
    provides access (e.g., signed CF).
    """
    return protected_access_url_response( request )

@csrf_exempt
@iframe_allow_any
def cookie_access( request, no_host_id, access_key ):
    """
    Respond to access request by redirecting to url that will set a cookie
    and then redirect response to the requested content under that url.
    """
    return protected_access_cookie_response( request, access_key )


"""-------------------------------------------------------------------
    Download content access request and response handler

    The download handler provides a file over HTTP, it is used both for
    direct downloads, and as the last step in multi-step downloads
    that eventually redirect to a file download.
"""

def _download_request_handler( url, **kwargs ):
    """
    Use the base path from the session, and add any additional path
    that was provided in the URL. This prevents reuse of the access session
    by trying to modify the URL below the original path, but allows LMS packages
    and other items that use relative paths.
    """
    log.debug("Download request handler: %s -> %s", url, kwargs)

    path_segments = url.strip('/').split('/')
    file_data = {}
    file_data['path'] = path_segments[:-1]
    file_data['file'] = path_segments[-1]
    file_data['attachment'] = kwargs.get('attachment')
    file_data['content_rev'] = kwargs.get('content_rev')

    return file_data, join_urls( *file_data['path'] )

set_access_request_handler( 'download', _download_request_handler )


def _download_response_handler( request, access_session ):
    """
    All file downloads use this code, including direct file downloads,
    and other types like video which may have an initial access response
    handler that then resolves to a download link.
    May be served from Cloudfront or nginx depending on configuration settings.
    Path is relative to the protected content download root, but should not
    include provider path as that will be added.
    """
    path = request.path
    log.debug("PROTECTED DOWNLOAD response: %s -> %s", path, access_session)

    # Make sure path and session line up
    key, key_path = parse_key_path( path )
    if key != access_session['key']:
        log.warning("SUSPECT - access_session url mismatch: %s -> %s -> %s",
                     request.mpipname, path, access_session)
        raise Http404

    filename = access_session['data']['file']
    attachment = access_session['data'].get('attachment')
    content_rev = access_session['data'].get('content_rev')

    # Setup the content-driven part of the access url
    url = download_path( access_session['data']['path'], key_path, filename )

    if content_rev:
        url = append_querystring( url, crev=content_rev )
    log.debug("Protected url: %s -> %s", request.mpipname, url)

    access_url = None
    if settings.MP_CLOUD:
        # Add S3 response-content-disposition for CF to pass through
        url = url_add_attachment( url, attachment )

        # Open delivery, CF url is used directly
        if use_open( access_session['delivery_mode'] ):
            access_url = cf_open_url( url )

        # Signed delivery
        elif cf_signed( request, access_session, url ):

            # Query string signing wraps url request and any querystring in a new
            # request with signing querystrings. Note this only works with single
            # file download, as signing query strings are gone after first request
            if use_querystring_url( access_session['delivery_mode'] ):
                access_url = cf_querystring_url( access_session, url )

            # Cloudfront signed cookie url - NOT the ultimate content access URL;
            # is a no-host request through cloudfront, which will set the cookie
            # and redirect to the actual protected CF link
            else:
                url = join_urls( settings.MP_URL_NO_HOST, access_session['sandbox'],
                            settings.MP_URL_PROTECTED, access_session['key'] )
                access_url = cf_url( access_session, url )
    else:
        # TEST HACK - serve as static from devserver for local test
        access_url = join_urls( settings.MP_URL_PROTECTED_XACCEL, url )

    if access_url:
        # Return a permanent redirect to to the content access url, which
        # is a temporary URL that lasts the life of the session
        response = HttpResponsePermanentRedirect( access_url )
        response['content-type'] = ''
        if settings.MP_IS_DJ_SERVER:
            log.info("DEV SERVE PROTECTED: %s ", access_url)
            # TEST HACK - redirect using Django static.serve and FileResponse
            # NOTE - FileResponse creates its own response, so content-disposition
            # cannot be set here
            # FUTURE - adapt static.serve and FileResponse to emulate MPF locally
        else:
            log.info3("PROTECTED SESSION URL: %s -> %s",
                        request.mpipname, access_url)
        return response

    # Otherwise files are served from nginx
    # Create relative bucket path through the AWS URL location
    # Policy on bucket has to accept request from this server
    # Redirects are done inside nginx using accel redirect
    return accel_redirect_protected( url, attachment=attachment )

set_access_response_handler( 'download', _download_response_handler )
