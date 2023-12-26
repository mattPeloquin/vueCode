#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Urls related to product screens
"""
from django.urls import re_path

from . import views
from . import api


user_patterns = [

    ]

boh_patterns = [

    re_path( r'^coupon$', views.coupon.profile_coupon, name='profile_coupon' ),
    re_path( r'^copy_product', views.copy.copy_product, name='copy_sandbox_product' ),

    ]

api_patterns = [

    re_path( r'^pa_info/(?P<pa_slug>[\w\.-]+)?[/]?$',
            api.pa_info, name='api_pa_info' ),
    re_path( r'^coupon_info/(?P<coupon_slug>[\w\.-]+)?[/]?$',
            api.coupon_info, name='api_coupon_info' ),

    ]

api_patterns_boh = [

    ]

root_patterns = [

    # Templates not reachable from urls
    re_path( r'^template/pa_success', views.testing.template_pa_success ),

    ]
