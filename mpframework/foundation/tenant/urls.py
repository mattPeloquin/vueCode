#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Urls for tenant customization support
"""
from django.urls import re_path

from mpframework.common import sys_options
from mpframework.common.view import mpTemplateView

from . import views


no_host_id_patterns = [

    re_path( r'^css_(?P<cache_url>[\w-]*)?$', views.edge_sandbox_css,
            name='edge_sandbox_css' ),

    ]

user_patterns = [

    re_path( r'^privacy[/]?$',
            mpTemplateView.as_view( template_name='tenant/privacy_page.html',
                    extra_context={
                        'no_robots': True,
                        'root_privacy': lambda: sys_options.root().html1,
                        }),
            name='privacy_display' ),
    re_path( r'^terms[/]?$',
            mpTemplateView.as_view( template_name='tenant/terms_page.html',
                    extra_context={
                        'no_robots': True,
                        'root_terms': lambda: sys_options.root().terms_html,
                        }),
            name='terms_display' ),
    ]
