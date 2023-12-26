#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Urls for LMS support
"""

from django.conf import settings
from django.urls import re_path

from . import views
from . import api


no_host_id_patterns = [

    re_path( r'^{}/(?P<access_key>[\w]+)[/]?$'.format( settings.MP_URL_PROTECTED ),
            views.cloudfront.cookie_access_lms, name='cookie_access_lms'),

    re_path( r'^user_items/.+$',
            api.cflms_origin_user_items, name='cflms_origin_user_items'),

    ]

api_patterns = [

    ]

api_patterns_boh = [

    re_path( r'^package_metrics$', api.package_metrics, name='api_package_metrics' ),

    ]

boh_patterns = [

    ]
