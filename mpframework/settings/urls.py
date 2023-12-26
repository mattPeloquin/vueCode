#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    MPF URLs

    Django urlpatterns object defines all URLs, MPF loads urls
    from apps into urlpatterns in this file.

    MPF URLs MUST BE COORDINATED WITH NGINX LOCATIONS!

    To support override of URLs by MPF extensions, modules are loaded in
    reverse platform order since Django uses first URL name.

    Well-known prefixes group urls for various purposes including
    server routing, nginx location filtering, tracking, maintainability,
    and url readability:
        bh       - Back of house servers (DJ admin, staff screens and apis)
        rt       - Root admin screens, mostly under rt/ad
        portal   - Customer portal
        ca       - Content access
        api      - Web api calls
        user     - Frontporch and user screens (mix of public, login)
        public   - Public api endpoints and landing pages
"""
import sys
from django.conf import settings
from django.urls import include
from django.urls import re_path

def _extend_urlpatterns():
    """
    Import url patterns for extension platforms.
    Naming conventions assumed in the module and urlpatterns names.
    """
    from mpframework.common.deploy.platforms import specialization_platforms
    urlpatterns = []
    for name in reversed( specialization_platforms() ):
        try:
            _locals = {}
            exec( 'from {0}.settings.urls import '
                        '{0}_urlpatterns as urlpatterns'
                    .format( name ), globals(), _locals  )
            urlpatterns += _locals['urlpatterns']
        except Exception as e:
            print("EXCEPTION LOADING PLATFORM URLs: %s -> %s" % (name, e))
            sys.exit(1)
    return urlpatterns

# Load extension url patterns and then core MPF patterns

urlpatterns = _extend_urlpatterns()

from ..foundation.ops import urls as ops_urls
from ..foundation.tenant import urls as tenant_urls
from ..user.mpuser import urls as user_urls
from ..content.mpcontent import urls as content_urls
from ..frontend.portal import urls as portal_urls

urlpatterns += [

    # Raw root patterns (slash handled in includes, portal last for catchall)
    re_path( r'^', include([
        re_path( r'^', include( ops_urls.raw_patterns ) ),
        re_path( r'^', include( portal_urls.raw_patterns ) ),
        ])),

    # Portal related links (slash handled in includes, portal last for catchall)
    re_path( r'^{}'.format( settings.MP_URL_PORTAL ), include([
        re_path( r'^', include( portal_urls.portal_patterns ) ),
        ])),

    # Public page support (slash handled in include files)
    re_path( r'^{}'.format( settings.MP_URL_PUBLIC ), include([
        re_path( r'^', include( content_urls.public_patterns ) ),
        ])),

    # Front porch, login and other public and login user screens
    # These need to be prefixed with a URL passed by Nginx and middleware
    # The user_urls patterns has a catch-all, so needs to be last
    re_path( r'^{}/'.format( settings.MP_URL_USER ), include([
        re_path( r'^', include( tenant_urls.user_patterns ) ),
        re_path( r'^', include( user_urls.user_patterns ) ),
        ])),

    # Protected content links
    re_path( r'^{}/|{}/'.format( settings.MP_URL_PROTECTED,
                              settings.MP_URL_PROTECTED_PASS ), include([
        re_path( r'^', include( content_urls.protected_patterns ) ),
        ])),
    re_path( r'^{}/'.format( settings.MP_URL_PROTECTED_FT ), include([
        ])),

    # No-host endpoints (used for various purposes)
    # Sandbox is loaded from URL path and added to request by sandbox middleware
    re_path( r'^{}/'.format( settings.MP_URL_NO_HOST_ID ), include([
        re_path( r'^', include( tenant_urls.no_host_id_patterns ) ),
        re_path( r'^', include( content_urls.no_host_id_patterns ) ),
        re_path( r'^', include( portal_urls.no_host_id_patterns ) ),
        ])),

    # Alternate server urls
    re_path( r'^{}/'.format( settings.MP_URL_FT ), include([
        ])),
    re_path( r'^{}/'.format( settings.MP_URL_BOH ), include([
        re_path( r'^ops/', include( ops_urls.boh_patterns )),
        ])),

    #-- APIs ---------------------------------------

    # Public API (never require user session)
    re_path( r'^{}/'.format( settings.MP_URL_API_PUBLIC ), include([
        re_path( r'^content/', include( content_urls.api_patterns_public ) ),
        re_path( r'^portal/', include( portal_urls.api_patterns_public ) ),
        ])),
    re_path( r'^{}/'.format( settings.MP_URL_API_PUBLIC_FT ), include([
        re_path( r'^ops/', include( ops_urls.api_patterns_public_ft ) ),
        ])),
    re_path( r'^{}/'.format( settings.MP_URL_API_PUBLIC_BOH ), include([
        re_path( r'^ops/', include( ops_urls.api_patterns_public_boh ) ),
        ])),

    # Normal APIs (usually require user session)
    re_path( r'^{}/'.format( settings.MP_URL_API ), include([
        re_path( r'^portal/', include( portal_urls.api_patterns ) ),
        ])),

    # Alternate server APIs
    re_path( r'^{}/'.format( settings.MP_URL_API_FT ), include([
        ])),
    re_path( r'^{}/'.format( settings.MP_URL_API_BOH ), include([
        re_path( r'^ops/', include( ops_urls.api_patterns_boh ) ),
        re_path( r'^user/', include( user_urls.api_patterns_boh ) ),
        re_path( r'^content/', include( content_urls.api_patterns_boh ) ),
        ])),

    ]

# Only load Django admin URLs when needed
if settings.MP_LOAD_ADMIN:
    from ..common.admin import root_admin
    from ..common.admin import staff_admin
    urlpatterns += [

        # Staff and Django admin urls
        re_path( r'^{}/'.format( settings.MP_URL_STAFF_ADMIN ), include([
            re_path( r'^', staff_admin.urls ),
            ])),

        # Root staff screens
        re_path( r'^{}/'.format( settings.MP_URL_ROOTSTAFF ), include([
            re_path( r'^ad/', root_admin.urls ),
            re_path( r'^op/', include( ops_urls.root_patterns ) ),
            ])),

        # External packages
        re_path( r'^{}/'.format( settings.MP_URL_EXTERNAL ), include([
            re_path( r'^nest/', include('nested_admin.urls') ),
            ])),

        ]

# For dev host protected files directly off local file system
if settings.MP_DEVWEB and not settings.MP_TESTING:
    import re
    from django.views import static
    _localprotected = r'^{}(?P<path>.*)$'.format(
                re.escape( settings.MP_URL_PROTECTED_XACCEL.lstrip('/') ))
    urlpatterns += [
        re_path( _localprotected, static.serve, kwargs={
                    'document_root': settings.MP_FOLDER_PROTECTED_LOCAL,
                    }),
        ]

"""--------------------------------------------------------------------
    Django error handlers

    When DEBUG is enabled, Django uses special error handling pages
    For non debug, non-test situations, use the handlers below
"""
if not settings.MP_TESTING:

    handler500 = 'mpframework.foundation.ops.views.errors.handle_500'
    handler400 = 'mpframework.foundation.ops.views.errors.handle_400'
    handler403 = 'mpframework.foundation.ops.views.errors.handle_403'
    handler404 = 'mpframework.foundation.ops.views.errors.handle_404'
