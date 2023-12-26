#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Login url extensions
"""
from django.urls import re_path

from . import views


"""
    Some patterns match empty values to provide base
    URLs for client-side JS concatonation.
"""
user_patterns = [

    # Site invite links that go to user create page
    re_path( r'^link/path/(?P<path>[\w\.\/-]*)[/]?$',
            views.login_path, name='login_path' ),
    re_path( r'^link/sku/(?P<sku>[\w\.-]*)[/]?$',
            views.login_sku, name='login_sku' ),
    re_path( r'^link/coupon/(?P<coupon_slug>[\w\.-]*)[/]?$',
            views.login_coupon, name='login_coupon' ),
    re_path( r'^link/content/(?P<content_slug>[\w\.-]*)[/]?$',
            views.login_content, name='login_content' ),

    # Show login anchored to a specific portal_content
    re_path( r'^c/(?P<content_slug>[\w\.-]*)[/]?$',
            views.login_portal_content, name='login_portal_content' ),

    # Links from the access dialog to login
    re_path( r'^access/(?P<sku>[\w\.-]*)[/]?$',
            views.login_access, name='login_access' ),
    re_path( r'^accessc/(?P<content_slug>[\w\.-]+)/(?P<sku>[\w\.-]*)[/]?$',
            views.login_portal_content_access, name='login_portal_content_access' ),

    # Popup login for use with iframe portal_contents
    re_path( r'^popup[/]?(?P<content_slug>[\w\.-]*)[/]?$',
            views.login_popup, name='login_popup' ),
    re_path( r'^popupa/(?P<content_slug>[\w\.-]+)/(?P<sku>[\w\.-]*)[/]?$',
            views.login_popup_access, name='login_popup_access' ),

    ]
