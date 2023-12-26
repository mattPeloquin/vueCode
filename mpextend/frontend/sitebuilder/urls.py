#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Sitebuilder urls
"""

from django.urls import re_path

from . import views


public_patterns = [

    re_path( r'^/p/(?P<landing_url>[\w]*)?$', views.landing.landing_page, name='landing_page' ),

    ]

boh_patterns = [

    re_path( r'^collection_links[/]?$', views.content.content_tree_links, name='content_tree_links' ),
    re_path( r'^item_links[/]?$', views.content.content_item_links, name='content_item_links' ),
    re_path( r'^coupon_links[/]?$', views.catalog.coupon_links, name='coupon_links' ),
    re_path( r'^sku_links[/]?$', views.catalog.sku_links, name='sku_links' ),
    re_path( r'^content_apis[/]?$', views.content.content_apis, name='content_apis' ),

    re_path( r'^cnames[/]?$', views.cnames.manage_cnames, name='manage_cnames' ),

    ]
