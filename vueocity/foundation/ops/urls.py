#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Owner urls
"""
from django.urls import re_path

from . import views
from .views import devops
from .views import reports


boh_patterns = [

    re_path( r'^billing', views.owner_billing, name='owner_billing' ),

    ]

root_patterns = [

    re_path( r'^new_tenant', devops.new_tenant, name='ops_new_tenant' ),
    re_path( r'^fixups', devops.fixups, name='ops_fixups' ),
    re_path( r'^caching', devops.caching, name='ops_caching' ),
    re_path( r'^events', devops.query_events, name='ops_events' ),
    re_path( r'^cleanups', devops.cleanups, name='ops_cleanups' ),

    re_path( r'^sites_csv$', reports.sites_csv, name='ops_sites_csv' ),

    ]
