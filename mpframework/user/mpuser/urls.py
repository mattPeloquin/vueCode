#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Urls for user profile screens
"""
from django.urls import re_path

from . import views
from . import api


user_patterns = [

    re_path( r'^logout[/]?$', views.logout.logout, name='logout' ),

    # Front porch login screens
    re_path( r'^login[/]?$', views.login.login, name='login' ),
    re_path( r'^create[/]?$', views.login.login_create, name='login_create' ),

    # New user confirmation dialog, with hash id sent to email
    re_path( r'^new_confirm/(?P<user_id_b64>[\w-]+)/(?P<extra_b64>[\w-]+)/(?P<token>[\w-]+)/$',
            views.activate.user_verify, name='user_verify' ),

    # Wrap Django behavior for managing password
    re_path( r'^pwd/reset[/]?$',
            views.password.mpPasswordResetView.as_view(), name='pwd_reset' ),
    re_path( r'^pwd/reset_sent/$',
            views.password.mpPasswordResetSentView.as_view(), name='pwd_reset_sent' ),
    re_path( r'^pwd/reset_confirm/(?P<user_id_b64>[\w-]+)/(?P<token>.+)/',
            views.password.mpPasswordResetConfirmView.as_view(), name='pwd_reset_confirm' ),
    re_path( r'^pwd/reset_complete/$',
            views.password.mpPasswordResetCompleteView.as_view(), name='pwd_reset_complete' ),
    re_path( r'^pwd/change_done/$',
            views.password.mpPasswordChangeDoneView.as_view(), name='pwd_change_done' ),

    # Acceptance of terms before accessing portal
    re_path( r'^accept_terms[/]?$', views.terms.accept_terms, name='terms_accept' ),
    re_path( r'^accept_terms/(?P<ename>[\w\.-]+)/(?P<evalue>[\w\.-]+)?[/]?$',
            views.terms.accept_terms, name='terms_accept_extra' ),

    # If email verification required and not done, show this
    re_path( r'^not_verified[/]?$', views.activate.not_verified, name='not_verified' ),
    re_path( r'^not_verified/(?P<ename>[\w\.-]+)/(?P<evalue>[\w\.-]+)?[/]?$',
            views.activate.not_verified, name='not_verified_extra' ),

    # Profile management
    re_path( r'^profile[/]?$', views.profile.manage_info, name='profile_manage' ),
    re_path( r'^security[/]?$', views.profile.update_security, name='profile_security' ),

    # Catch-all to send to login screen rather than 404
    re_path( r'^.*$', views.login.login ),

    ]

api_patterns_boh = [

    re_path( r'^set_mode$', api.update.set_delivery_mode, name='api_user_delivery_mode' ),

    ]
