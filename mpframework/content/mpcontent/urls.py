#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Urls for base content support
"""
from django.conf import settings
from django.urls import re_path

from . import views
from . import api


protected_patterns = [

    # Default catch-all URL for protected content access
    re_path( r'^.+$', views.protected.url_access, name='url_access'),

    ]

no_host_id_patterns = [

    re_path( r'^{}/(?P<access_key>[\w]+)[/]?$'.format( settings.MP_URL_PROTECTED ),
            views.protected.cookie_access, name='cookie_access'),

    ]

public_patterns = [

    re_path( r'^/desc/(?P<content_slug>[\w\.-]+)?[/]?$',
            views.public.content_description,  name='content_description' ),
    re_path( r'^/image/(?P<content_slug>[\w\.-]+)?[/]?$',
            views.public.content_image, name='content_image' ),

    ]

api_patterns_public = [

    # Get a url for playing an item; overridden in MPF extensions
    re_path( r'^item_access$', api.item_access, name='api_item_access' ),

    re_path( r'^full/(?P<content_slug>[\w\.-]+)?[/]?$',
            api.content_full, name='api_content_full' ),

    re_path( r'^partial/(?P<content_slug>[\w\.-]+)?[/]?$',
            api.content_partial, name='api_content_partial' ),

    re_path( r'^$', api.get_content, name='api_get_content' ),

    ]

api_patterns_boh = [

    re_path( r'^item_add$', api.item_add, name='api_item_add' ),
    re_path( r'^tree_set_workflow$',
            api.tree_set_workflow, name='tree_set_workflow' ),
    re_path( r'^tree_set_sandboxes$',
            api.tree_set_sandboxes, name='tree_set_sandboxes' ),
    re_path( r'^tree_rebuild$', api.tree_rebuild, name='tree_rebuild' ),

    ]
