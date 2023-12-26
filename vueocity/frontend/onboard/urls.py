#--- Vueocity Platform, Copyright 2021 Vueocity, LLC
"""
    Onboarding URLs
"""
from django.urls import re_path

from . import views
from . import api


public_ft_patterns = [

    # Create new provider account in system
    re_path( r'^onboard_signup$', views.signup.onboard_signup, name='onboard_signup' ),
    re_path( r'^onboard_create/(?P<token>[\w-]+)/?$', views.create.onboard_create,
            name='onboard_create' ),
    re_path( r'^onboard_login/(?P<token>[\w-]+)/?$', views.login.onboard_login,
            name='onboard_login' ),

    re_path( r'^portal_random/(?P<option>[\w-]*)?[/]?.*$',
            views.portal_tool.easy_portal_random,
            name='easy_portal_random' ),
    re_path( r'^portal_next/(?P<current_theme>[\w-]*)?[/]?.*$',
            views.portal_tool.easy_portal_next_theme,
            name='easy_portal_next_theme' ),

    re_path( r'^portal_site_save.*$', views.portal_tool.easy_portal_site_save,
            name='easy_portal_site_save' ),
    re_path( r'^portal_theme_save.*$',
            views.portal_tool.easy_portal_theme_save, name='easy_portal_theme_save' ),

    re_path( r'^portal_all/(?P<portal_url>.*)?$',
            views.portal_tool.easy_portal_all, name='easy_portal_all' ),
    re_path( r'^portal/(?P<portal_url>.*)?$',
            views.portal_tool.easy_portal, name='easy_portal' ),

    re_path( r'^portal.*$', views.portal_tool.easy_portal, name='easy_portal_root' ),

    ]

ft_patterns = [

    re_path( r'^change_level$', views.levels.change_level, name='change_level' ),

    ]

boh_patterns = [

    re_path( r'^easy/sandbox$', views.sandbox.easy_sandbox, name='easy_sandbox' ),
    re_path( r'^easy/portal_color$',
            views.portal_color.easy_portal_color, name='easy_portal_color' ),
    re_path( r'^easy/add_product$',
            views.add_product.easy_add_product, name='easy_add_product' ),

    ]

api_patterns_public_ft = [

    re_path( r'^domain/(?P<subdomain>[\w-]*)$', api.domain_check,
            name='api_domain_check' ),

    ]

root_patterns = [

    re_path( r'^onboard$', views.testing.mptest_onboard, name='mptest_onboard'),

    ]
