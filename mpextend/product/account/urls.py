#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Urls related to product screens
"""
from django.urls import re_path

from . import views
from . import api


user_patterns = [

    re_path( r'^access_select$', views.access_select, name='access_select' ),

    # Group invite functionality
    re_path( r'^invite/(?P<ga_id>[\w]+)/(?P<apa_id>[\w-]+)[/]?$',
            views.ga_login_apa, name='ga_login_apa' ),
    re_path( r'^invitec/(?P<ga_id>[\w]+)/(?P<coupon_slug>[\w-]+)[/]?$',
            views.ga_login_coupon, name='ga_login_coupon' ),
    re_path( r'^invite/(?P<ga_id>[\w]+)[/]?$',
            views.ga_login, name='ga_login' ),

    ]

boh_patterns = [

    # Group Account admin screens
    re_path( r'^group/overview/(?P<ga_id>[\w]+)?[/]?$',
            views.ga_overview, name='ga_overview' ),
    re_path( r'^group/invite/(?P<ga_id>[\w]+)?[/]?$',
            views.ga_invite, name='ga_invite' ),
    re_path( r'^group/users/(?P<ga_id>[\w]+)?[/]?$',
            views.ga_users_summary, name='ga_users_summary' ),
    re_path( r'^group/licenses/(?P<ga_id>[\w]+)?[/]?$',
            views.ga_licenses, name='ga_licenses' ),
    re_path( r'^group/content/(?P<ga_id>[\w]+)?[/]?$',
            views.ga_content, name='ga_content' ),
    re_path( r'^group/settings/(?P<ga_id>[\w]+)?[/]?$',
            views.ga_settings, name='ga_settings' ),

    ]

api_patterns_public = [

    re_path( r'^access_options$', api.access_options, name='api_access_options' ),
    re_path( r'^access_apas$', api.access_apas, name='api_access_apas' ),

    ]
