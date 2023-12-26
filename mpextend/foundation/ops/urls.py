#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Ops extension urls
"""
from django.urls import re_path

from . import views


raw_patterns = [

    # System root urls that are built out for each site
    re_path( r'^robots.txt$', views.sandbox_robots, name='sandbox_robots' ),
    re_path( r'^sitemap.xml$', views.sandbox_sitemap, name='sandbox_sitemap' ),
    re_path( r'^service_worker.js$', views.sandbox_service_worker,
            name='sandbox_service_worker' ),
    re_path( r'^manifest.webmanifest$', views.sandbox_pwa_manifest ),
    re_path( r'^manifest.json$', views.sandbox_pwa_manifest,
            name='sandbox_pwa_manifest' ),

    ]
