#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    mpExtend URLs, which are added to MPF URLS
"""
from django.conf import settings
from django.urls import re_path
from django.urls import include

from ..user.mpuser import urls as mpuser_urls
from ..user.plan import urls as plan_urls
from ..user.usercontent import urls as uc_urls
from ..user.sso import urls as sso_urls
from ..user.tracking import urls as ut_urls
from ..frontend.portal import urls as portal_urls
from ..foundation.reports import urls as report_urls
from ..frontend.sitebuilder import urls as sitebuilder_urls
from ..foundation.ops import urls as ops_urls
from ..content.mpcontent import urls as mpcontent_urls
from ..content.lms import urls as lms_urls
from ..content.video import urls as video_urls
from ..content.proxy import urls as proxy_urls
from ..product.account import urls as account_urls
from ..product.catalog import urls as catalog_urls
from ..product.payment import urls as payment_urls

# Load content urls to trigger registering protected view handlers
from mpextend.content.mpcontent import urls

mpextend_urlpatterns = [

    # Raw root patterns (slash handled in include files)
    re_path( r'^', include([
        re_path( r'^', include( ops_urls.raw_patterns ) ),
        ])),

    # Portal page support (slash handled in include files)
    re_path( r'^{}'.format( settings.MP_URL_PORTAL ), include([
        re_path( r'^', include( portal_urls.portal_patterns ) ),
        ])),

    # Public page support (slash handled in include files)
    re_path( r'^{}'.format( settings.MP_URL_PUBLIC ), include([
        re_path( r'^', include( sitebuilder_urls.public_patterns ) ),
        ])),
    re_path( r'^{}'.format( settings.MP_URL_PUBLIC_FT ), include([
        ])),

    # User screens
    re_path( r'^{}/'.format( settings.MP_URL_USER ), include([
        re_path( r'^', include( mpuser_urls.user_patterns ) ),
        re_path( r'^catalog/', include( catalog_urls.user_patterns ) ),
        re_path( r'^account/', include( account_urls.user_patterns ) ),
        ])),

    # Back of house server pages
    re_path( r'^{}/'.format( settings.MP_URL_BOH ), include([
        re_path( r'^lms/', include( lms_urls.boh_patterns ) ),
        re_path( r'^video/', include( video_urls.boh_patterns ) ),
        re_path( r'^catalog/', include( catalog_urls.boh_patterns )),
        re_path( r'^account/', include( account_urls.boh_patterns )),
        re_path( r'^payment/', include( payment_urls.boh_patterns ) ),
        re_path( r'^sb/', include( sitebuilder_urls.boh_patterns ) ),
        re_path( r'^user/', include( ut_urls.boh_patterns ) ),
        re_path( r'^plan/', include( plan_urls.boh_patterns ) ),
        ])),

    # Protected access specializations
    re_path( r'^{}/'.format( settings.MP_URL_PROTECTED ), include([
        ])),
    re_path( r'^{}/'.format( settings.MP_URL_PROTECTED_FT ), include([
        re_path( r'^', include( proxy_urls.protected_ft_patterns ) ),
        ])),

    # No-host extensions
    re_path( r'^{}/'.format( settings.MP_URL_NO_HOST_ID ), include([
        re_path( r'^lms/', include( lms_urls.no_host_id_patterns ) ),
        ])),
    re_path( r'^{}/'.format( settings.MP_URL_NO_HOST_FT ), include([
        re_path( r'^payment/', include( payment_urls.no_host_root_patterns ) ),
        ])),

    # API endpoints
    re_path( r'^{}/'.format( settings.MP_URL_API_PUBLIC ), include([
        re_path( r'^content/', include( mpcontent_urls.api_patterns_public ) ),
        re_path( r'^account/', include( account_urls.api_patterns_public ) ),
        re_path( r'^sso/', include( sso_urls.api_patterns_public ) ),
        ])),
    re_path( r'^{}/'.format( settings.MP_URL_API ), include([
        re_path( r'^catalog/', include( catalog_urls.api_patterns ) ),
        re_path( r'^lms/', include( lms_urls.api_patterns ) ),
        re_path( r'^plan/', include( plan_urls.api_patterns ) ),
        re_path( r'^uc/', include( uc_urls.api_patterns ) ),
        re_path( r'^user/', include( ut_urls.api_patterns ) ),
        re_path( r'^sso/', include( sso_urls.api_patterns ) ),
        ])),
    re_path( r'^{}/'.format( settings.MP_URL_API_BOH ), include([
        re_path( r'^catalog/', include( catalog_urls.api_patterns_boh ) ),
        re_path( r'^payment/', include( payment_urls.api_patterns_boh ) ),
        re_path( r'^lms/', include( lms_urls.api_patterns_boh ) ),
        re_path( r'^report/', include( report_urls.api_patterns_boh ) ),
        re_path( r'^uc/', include( uc_urls.api_patterns_boh ) ),
        re_path( r'^user/', include( ut_urls.api_patterns_boh ) ),
        ])),

    # Root, debug, testing
    re_path( r'^{}/'.format( settings.MP_URL_ROOTSTAFF ), include([
        re_path( r'^pay/', include( payment_urls.root_patterns ) ),
        re_path( r'^cat/', include( catalog_urls.root_patterns ) ),
        ])),

    ]
