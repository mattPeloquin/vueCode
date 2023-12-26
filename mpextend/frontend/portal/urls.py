#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Portal url extensions
"""
from django.urls import re_path

from . import views


portal_patterns = [

    # "Extra" portal processing at supports passing parameters to
    # setup a portal load
    re_path( r'^e/(?P<ename>[\w]+)/(?P<evalue>[\w\.\/%-]+)[/]?$',
            views.portal_extra, name='portal_extra' ),

    # Portal page URLs for linking/embedding collection and items with
    # theme, frame, and extra options

    re_path( r'^c/(?P<content_slug>[\w\.-]+)/e/(?P<ename>[\w]+)/(?P<evalue>[\w\.%-]+)/$',
            views.portal_content_extra, name='portal_content_extra' ),
    re_path( r'^t(?P<theme_id>[0-9]+)/c/(?P<content_slug>[\w\.-]+)/e/(?P<ename>[\w]+)/(?P<evalue>[\w\.%-]+)/$',
            views.portal_content_extra, name='portal_content_theme_extra' ),
    re_path( r'^v(?P<frame_id>[0-9]+)/c/(?P<content_slug>[\w\.-]+)/e/(?P<ename>[\w]+)/(?P<evalue>[\w\.%-]+)/$',
            views.portal_content_extra, name='portal_content_frame_extra' ),

    re_path( r'^c/(?P<content_slug>[\w\.-]*)[/]?.*$',
            views.portal_content, name='portal_content' ),
    re_path( r'^t(?P<theme_id>[0-9]+)/c/(?P<content_slug>[\w\.-]*)[/]?.*$',
            views.portal_content, name='portal_content_theme' ),
    re_path( r'^v(?P<frame_id>[0-9]+)/c/(?P<content_slug>[\w\.-]*)[/]?.*$',
            views.portal_content, name='portal_content_frame' ),

    ]
