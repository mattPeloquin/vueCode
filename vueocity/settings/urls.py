#--- Vueocity platform, Copyright 2021 Vueocity LLC
"""
    Vueocity URLs
"""
from django.conf import settings
from django.urls import re_path
from django.urls import include

from ..foundation.ops import urls as ops_urls
from ..frontend.onboard import urls as onboard_urls


# Platform-specific URLs will override MPF urls if needed
vueocity_urlpatterns = [

    re_path( r'^{}/'.format( settings.MP_URL_FT ), include([
        re_path( r'^ob/', include( onboard_urls.ft_patterns ) ),
        ])),
    re_path( r'^{}/'.format( settings.MP_URL_PUBLIC_FT ), include([
        re_path( r'^ob/', include( onboard_urls.public_ft_patterns ) ),
        ])),
    re_path( r'^{}/'.format( settings.MP_URL_API_PUBLIC_FT ), include([
        re_path( r'^ob/', include( onboard_urls.api_patterns_public_ft ) ),
        ])),

    re_path( r'^{}/'.format( settings.MP_URL_BOH ), include([
        re_path( r'^ops/', include( ops_urls.boh_patterns ) ),
        re_path( r'^ob/', include( onboard_urls.boh_patterns ) ),
        ])),

    re_path( r'^{}/'.format( settings.MP_URL_ROOTSTAFF ), include([
        re_path( r'^op/', include( ops_urls.root_patterns ) ),
        re_path( r'^ob/', include( onboard_urls.root_patterns ) ),
        ])),

    ]
