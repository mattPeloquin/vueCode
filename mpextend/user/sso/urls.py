#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    SSO  urls
"""
from django.urls import re_path

from . import api


api_patterns_public = [

    re_path( r'^signin$', api.sso_signin, name='api_sso_signin' ),

    ]

api_patterns = [

    ]
