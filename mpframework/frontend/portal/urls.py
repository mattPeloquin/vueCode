#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Portal urls
"""
from django.urls import re_path

from . import views
from . import api


raw_patterns = [
    # Root of sandbox site can be configured
    re_path( r'^$', views.home.site_home, name='site_home' ),
    ]

portal_patterns = [
    # Set portal options via redirect
    re_path( r'^opts/(?P<options>.+)$',
            views.portal_user_options, name='portal_user_options' ),

    re_path( r'^t(?P<theme_id>[0-9]+).*$',
            views.portal_view, name='portal_theme' ),
    re_path( r'^v(?P<frame_id>[0-9]+).*$',
            views.portal_view, name='portal_frame' ),

    # Default portal url for portal configured for sandbox
    # Acts as a catchall for all portal URLs, nav deeplinking happens in portal JS
    re_path( r'^.*$', views.portal_view, name='portal_view' ),
    ]

no_host_id_patterns = [
    re_path( r'^bootstrap/content_(?P<cache_url>[\w\.-]*)?$',
            api.edge_bootstrap_content, name='edge_bootstrap_content' ),
    ]

api_patterns_public = [
    re_path( r'^bootstrap/delta$', api.bootstrap_delta, name='bootstrap_delta' ),
    re_path( r'^bootstrap/content_(?P<cache_url>[\w\.-]*)?$',
            api.bootstrap_content, name='bootstrap_content' ),
    ]

api_patterns = [
    re_path( r'^bootstrap/user_(?P<cache_url>[\w\.-]*)?$',
            api.bootstrap_user, name='bootstrap_user' ),
    re_path( r'^bootstrap/nocache$', api.bootstrap_nocache, name='bootstrap_nocache' ),
    ]
