#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    User-content urls
"""
from django.urls import re_path

from . import api


api_patterns = [

    re_path( r'^user_content$', api.user_content, name='api_user_content' ),
    re_path( r'^user_items[/\w]+$', api.user_item, name='api_user_item' ),

    ]

api_patterns_boh = [

    re_path( r'^update_version$', api.update_version, name='api_update_version' ),

    ]
