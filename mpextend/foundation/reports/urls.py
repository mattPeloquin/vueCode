#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Report urls
"""
from django.urls import re_path

from . import accounts
from . import users


api_patterns_boh = [

    # Account admin csv reports
    re_path( r'^ga_summary_csv/(?P<ga_id>[\w]+)?[/]?$',
                accounts.ga_summary_csv, name='ga_summary_csv' ),
    re_path( r'^ga_purchases_csv/(?P<ga_id>[\w]+)?[/]?$',
                accounts.ga_purchases_csv, name='ga_purchases_csv' ),
    re_path( r'^ga_content_top_csv/(?P<ga_id>[\w]+)?[/]?$',
                accounts.ga_content_top_csv, name='ga_content_top_csv' ),
    re_path( r'^ga_content_csv/(?P<ga_id>[\w]+)?[/]?$',
                accounts.ga_content_csv, name='ga_content_csv' ),

    # Staff reports
    re_path( r'^users_summary_csv/?(?P<start>[\w]+)?[/]?$',
                users.users_summary_csv, name='users_summary_csv' ),
    re_path( r'^users_licenses_csv/?(?P<start>[\w]+)?[/]?$',
                users.users_licenses_csv, name='users_licenses_csv' ),
    re_path( r'^users_content_csv/?(?P<start>[\w]+)?[/]?$',
                users.users_content_csv, name='users_content_csv' ),
    re_path( r'^users_content_top_csv/?(?P<start>[\w]+)?[/]?$',
                users.users_content_top_csv, name='users_content_top_csv' ),

    ]
