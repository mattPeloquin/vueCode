#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Urls related to user extensions
"""
from django.urls import re_path

from . import views
from . import api


boh_patterns = [

    re_path( r'^dashboard$', views.dashboard.user_dashboard, name='user_dashboard' ),

    # User profile screens
    re_path( r'^history$', views.history.profile_history, name='profile_history' ),

    ]

api_patterns = [

    re_path( r'^ui_state$', api.ui_state.set_ui_state, name='api_user_ui_state' ),

    ]

api_patterns_boh = [

    re_path( r'^tracking$', api.tracking.get_active_users, name='api_tracking_active_users' ),

    ]
