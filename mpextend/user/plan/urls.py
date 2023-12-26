#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Plan Urls
"""
from django.urls import re_path

from . import api
from . import views


boh_patterns = [

    # User profile screens
    re_path( r'^user_plans$', views.user_plans, name='user_plans' ),

    # Group account admin screens
    re_path( r'^admin_plans/(?P<account_id>[\w]+)?[/]?$',
                views.ga_plans, name='ga_plans' ),

    ]

api_patterns = [

    re_path( r'^plans$', api.plans, name='api_plans' ),
    re_path( r'^tree_plan$', api.tree_plan, name='api_tree_plan' ),

    ]
