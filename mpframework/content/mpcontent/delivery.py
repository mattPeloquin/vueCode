#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    All requests for protected content flow through functions in this file

    Depending on the content type and configuration settings, requests for protected
    content generate different HTTP responses. Many types of access involve
    multiple redirects (e.g., to setup a player and then download file for it).

    Content type, access type, and options define the request-response flow
    (e.g., download a file vs. setup a video player that then downloads a file)
    through the use of 'handlers'.
    Different content have different access types available, and may add
    constraints (e.g., LMS content can only be delivered in certain ways).

    Delivery mode adjusts how the HTTP response is made available to the browser
    (e.g., CloudFront cookies vs. query strings). Delivery mode is constrained by
    access and compatibility settings for the sandbox, accounts, and users.
    The HTTP response may also be adjusted by browser type.

    Each protected content access request is first checked for valid access/license.
    On approval the delivery process creates a cached 'access session' with
    token/key that holds temporary info related to the access. Then different
    responses occur based on delivery mode:

    1a) Cloudfront signed cookie redirect
    The initial request generates a redirect to a Cloudfront origin URL, which is
    necessary to add a signed cookie to the CF URL. Then new requests for content
    access can be made through the CF url with the signed cookie attached.
    Any relative references (LMS loading files) or partial requests (mp4 streaming)
    will go directly to CF while the cookies are active.

    This is typically the preferred mode, to send most traffic through CF.

    1b) Cloudfront signed querystring redirect
    Redirects to resource on Cloudfront using a signed url. Unlike the signed cookie
    handoff, any derived calls for more content are run through MPF
    (not including streaming calls).

    Useful for compatibility in cases where CF cookies are stripped or can't be
    set, such as running under CNAME and Safari (which won't set cookies).
    Query strings can't support relative downloads such as LMS that need to load
    additional content into their own IFrame, because query string gets lost.

    2) NGINX accel-redirect to URL
    Use accel-redirect to get the file from the given URL and serve it, ensuring all
    subsequent requests from the content are seen by MPF instead of CDN.
    Can provide more security by checking session for every request
    and ensures the domain for the requested urls is the same.
    Efficiency of caching will depend how Nginx is deployed.

      2a) NGINX may be configured to recognize certain file types and serve
      them without contacting Django at all. This is used with the LMS delivery
      to optimize for items that don't need protection (e.g., js, images).

    3) Open public link
    A link to protected content that flows through a public Cloudfront link may
    be provided as a last-ditch compatibility mechanisms.

    FUTURE - Open links need to be coupled with making copies of content on
    S3 that is versioned and time-limited, to limit exposure of these links.

    General notes:
     - CF distributions must be properly configured for signing and origins
     - Can't use LMS SCORM iframe content unless the url redirected to is the
       same as originator because LMS JS wrapper will throw security error.
     - Dev configurations just redirect to local links.
"""
from django.conf import settings
from django.http import Http404
from django.http import HttpResponseRedirect
from django.core.cache import caches

from mpframework.common import log
from mpframework.common.aws.s3 import url_add_attachment
from mpframework.common.utils import now
from mpframework.common.utils import get_random_key
from mpframework.common.utils import join_urls
from mpframework.common.utils.http import append_querystring
from mpframework.common.utils.user import session_cookie_name
from mpframework.user.mpuser.models import mpUser

from .utils.delivery_utils import *


_cache = caches['session']


# Per-server cache of request and response content handlers

def set_access_request_handler( access_type, handler ):
    _request_handlers[ access_type ] = handler
_request_handlers = {}

def set_access_response_handler( access_type, handler ):
    _response_handlers[ access_type ] = handler
_response_handlers = {}


#-------------------------------------------------------------------
# First, a request to access protected content generates an access session
# stored in cache and returns a URL to start the access...

def create_access_url( request, access_type, data, **kwargs ):
    """
    Create cached access session for a protected request
    Returns 'content access' url for accessing that session
    Caching timeout determines lifetime of access session for the user
    """

    # Remove kwargs that shouldn't be passed to handler
    key = kwargs.pop( 'key', get_random_key( prefix='ar' ) )
    url_prefix = kwargs.pop( 'url_prefix', settings.MP_URL_PROTECTED )

    # Call request handler to update access_session data and end of url (if needed)
    handler = _request_handlers.get( access_type, _default_request_handler )
    data, url_end = handler( data, **kwargs )

    # Items can override default delivery mode, while user setting trumps all
    mode = request.user.delivery_mode( default=kwargs.get('default_mode') )
    if mode not in DELIVERY_TYPES:
        mode = DELIVERY_DEFAULT

    url = join_urls( url_prefix, key, url_end,
                prepend_slash=True, append_slash=True )
    access_session = {
        'key': key,
        'sandbox': request.sandbox.pk,
        'url': url,
        'user': request.user.pk,
        'user_session': request.session.session_key,
        'delivery_mode': mode,
        'compat_urls': request.user.use_compat_urls,
        'timeout': _url_timeout( request.sandbox, mode ),
        'start': now(),
        'ip': request.ip,
        'access_type': access_type,
        'data': data,
        }
    set_access_session( access_session )

    log.debug("Created access session: %s -> %s", request.mpname, access_session)
    return url

def set_access_session( access_session ):
    """
    Place/overwrite access session into user cache for access by subsequent calls
    """
    if access_session['timeout'] > 0:
        _cache.set( _cache_key( access_session['sandbox'], access_session['key'] ),
                    access_session, access_session['timeout'] )

def get_access_session( sandbox_id, key ):
    return _cache.get( _cache_key( sandbox_id, key ) )

"""-------------------------------------------------------------------
    ...Next, create response for the content access request. Behavior
    varies based handler defined for content and delivery options. In many
    cases, a response will generate another content access url to load
    the content (e.g., setting up player in iframe, then loading file).

    Protected requests are often GETs, but other requests can be made (e.g, proxy).

    Cookie responses need to set signed cookies from the URL the protected
    content is served from (e.g., CF), so need a 2-step redirect to do so.
"""

def protected_access_url_response( request ):
    """
    Returns HTTP response based on the content's response handler, e.g., hosting files
    through Cloudfront, direct downloads, proxy calls, etc.

    User access is checked based on sandbox options. Due to option for open
    protection to work around losing session cookies, request/user may NOT be
    authenticated at this point.
    The link fails if the session has expired or any secure access options fail.
    """
    sandbox = request.sandbox
    user = request.user
    access_key, _path = parse_key_path( request.path )
    assert sandbox and user and access_key

    access_session = get_access_session( sandbox.pk, access_key )
    if not access_session:
        log.info2("ACCESS url EXPIRED: %s -> %s", request.mpipname, access_key)
        raise Http404

    if _has_access( sandbox, user, access_session ):
        log.info3("Default access: %s, %s -> %s", request.mpipname,
                    access_key, access_session['access_type'])

        handler = _response_handlers.get( access_session['access_type'] )

        log.debug("Access session response: %s -> %s", handler, request.path)
        if handler:
            # If user session is missing and compatibility mode is on, attach user
            if not user.is_ready() and use_no_auth( access_session['delivery_mode'] ):
                user_id = access_session['user']
                if user_id:
                    request.user = mpUser.objects.get_from_id( sandbox, user_id )
                    log.info2("ACCESS compatibility added user back to request: %s -> %s",
                               request.user, _path)

            return handler( request, access_session )

    log.info("ACCESS url DENIED: %s -> %s", request.mpipname, access_session)
    raise Http404

def protected_access_cookie_response( request, access_key, **kwargs ):
    """
    Returns an HTTP redirect response, that will setup CF signed cookies on a no-host
    CF URL. Then the access url originally stored in the access session is called.
    This request will not have a user session associated with it, so user session is
    added back from the session information.
    If access isn't allowed, raise 404 instead of login redirect, since request was
    made on CF vs. MPF url and response is likely in an iframe.
    """
    sandbox = request.sandbox
    access_session = get_access_session( sandbox.pk, access_key )
    if not access_session:
        log.info2("ACCESS cookie EXPIRED: %s -> %s", request.mpipname, access_key)
        raise Http404

    # Update request with user from from access session; support visitor access
    if access_session['user'] is None:
        user = request.user
    else:
        user = mpUser.objects.get_from_id( sandbox, access_session['user'] )
        request.user = user

    # Setup the response for users with access
    if _has_access( sandbox, user, access_session ):
        log.info3("CF cookie access: %s, %s, %s", request.mpipname, user, access_key)

        response_fn = kwargs.get( 'response_fn', _default_cloudfront_response )
        response = response_fn( request, access_session )

        cf_add_cookies_response( access_session, response )

        # Add the user session in case calls to Django will be made
        response.set_cookie( session_cookie_name( sandbox ),
                    access_session['user_session'], httponly=True,
                    secure=True, samesite=cf_samesite( access_session ) )

        log.debug("Protected CF cookie: %s -> %s", request.mpipname, response.url)
        return response

    log.info("ACCESS cookie DENIED: %s -> %s", request.mpipname, access_session)
    raise Http404

#-------------------------------------------------------------------

def _cache_key( id, key ):
    return 'access{}_{}'.format( id, key )

def _default_request_handler( data, **kwargs ):
    log.debug2("Default request handler: %s", data)
    return data, ''

def _default_cloudfront_response( _request, access_session ):
    """
    This is the CF origin response for protected access, which
    redirects to CF protected url with cookies attached.
    """
    data = access_session['data']
    path = download_path( data['path'], '', data['file'] )
    url = cf_url( access_session, path )
    url = url_add_attachment( url, access_session['data'].get('attachment') )
    content_rev = access_session['data'].get('content_rev')
    if content_rev:
        url = append_querystring( url, crev=content_rev )
    return HttpResponseRedirect( url )

def _has_access( sandbox, user, access_session ):
    """
    Determine whether the access session is valid for the user
    """
    if not user.has_sandbox_access( sandbox ) or sandbox.pk != access_session['sandbox']:
        log.warning("SUSPECT - access_session mismatch: %s, %s -> %s",
                        sandbox, user, access_session)
        return False

    if use_no_auth( access_session['delivery_mode'] ):
        log.debug2("Access compatibility delivery: %s -> %s", user, access_session)
        return True

    if user.is_ready():
        if user.pk == access_session['user']:
            log.debug2("Granting access to ready user: %s", user)
            return True
        else:
            log.warning("SUSPECT - user request/access mismatch: %s -> %s",
                         user, access_session)
            return False

    if access_session['user'] is None:
        log.debug2("Granting access to visitor for public access: %s", user)
        return True

    log.debug("Denying access due to user and access session: %s -> %s",
              sandbox, access_session['user'])

def _url_timeout( sandbox, mode ):
    """
    Determine timeout for signed url access
    """
    rv = sandbox.options['access.timeout']
    if not rv:
        rv = settings.MP_PROTECTED['SECONDS']
    if mode.startswith( DELIVERY_PROT ):
        rv = rv // 3
    return rv
