#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Urls for LMS support
"""

from django.urls import re_path

from . import views


protected_ft_patterns = [

    re_path( r'^pc(?P<cache_id>[0-9]+)(/.+)?$',
            views.protected_proxy_cache, name='protected_proxy_cache' ),

    ]
