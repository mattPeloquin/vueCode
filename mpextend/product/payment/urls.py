#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Urls related to product screens
"""
from django.urls import re_path

from . import api
from . import views


no_host_root_patterns = [

    # Callback
    re_path( r'^authlink/(?P<paytype>[\w]+)[/]?',
            views.setup.payment_authlink, name='payment_authlink' ),
    ]

boh_patterns = [

    re_path( r'^setup/(?P<paytype>[\w]+)?[/]?$',
            views.setup.payment_setup, name='payment_setup' ),

    re_path( r'^start/(?P<apa_id>[\w]+)/(?P<paytype>[\w]+)?[/]?$',
            views.start.payment_start, name='payment_start' ),

    # Callbacks from payment services, which may have varied URL endings
    re_path( r'^error/(?P<paytype>[\w]+)[/]?',
            views.error.payment_error, name='payment_error' ),
    re_path( r'^cancel/(?P<paytype>[\w]+)[/]?',
            views.cancel.payment_cancel, name='payment_cancel' ),
    re_path( r'^finish/(?P<paytype>[\w]+)[/]?',
            views.finish.payment_finish, name='payment_finish' ),

    ]

api_patterns_boh = [

    re_path( r'^setups[/]?$',
            api.setup.payment_setups, name='api_payment_setups' ),
    re_path( r'^setup/(?P<paytype>[\w]+)[/]?$',
            api.setup.payment_setup, name='api_payment_setup' ),

    re_path( r'^options/(?P<apa_id>[\w]+)[/]?$',
            api.options.api_payment_options, name='api_payment_options' ),
    re_path( r'^start/(?P<apa_id>[\w]+)/(?P<paytype>[\w]+)?[/]?$',
            api.start.api_payment_start, name='api_payment_start' ),

    ]

root_patterns = [

    re_path( r'^paypal$', views.testing.mptest_paypal, name='mptest_paypal'),
    re_path( r'^stripe$', views.testing.mptest_stripe, name='mptest_stripe'),

    ]
