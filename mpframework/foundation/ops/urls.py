#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Ops URLs include shared services and root support items
"""
from django.conf import settings
from django.urls import re_path

from . import views
from .views import devops
from .views import testing
from .api import autolookup
from .api import editor
from .api import direct
from .api import widgets


raw_patterns = [

    re_path( r'^favicon.ico$', views.sandbox_favicon, name='sandbox_favicon' ),

    re_path( r'^{}'.format( settings.MP_HEALTHCHECK_URL ),
            views.health_ping, name='health_ping' ),

    ]

api_patterns_public_ft = [

    re_path( r'^country_options$',
            widgets.country_options, name='api_country_options' ),

    ]

api_patterns_public_boh = [

    re_path( r'^bmsg', views.browser_message, name='browser_message' ),

    ]

boh_patterns = [

    re_path( r'^editor$', views.html_editor_frame,  name='html_editor_frame' ),

    ]

_upload_args = '(?P<protected>[\w\.-]+)[/]?$'
api_patterns_boh = [

    re_path( r'^lookup$', autolookup.Autolookup.as_view(),
            name='api_autolookup_model'),

    # Direct S3 upload
    re_path( r'^s3/upload/', direct.upload_metadata, name='upload_metadata'),
    re_path( r'^s3/v4sig/', direct.upload_signature, name='upload_signature'),

    # Editor upload
    re_path( r'^upload_file/%s' % _upload_args, editor.upload_file, name='editor_upload_file' ),
    re_path( r'^upload_image/%s' % _upload_args, editor.upload_file, { 'image': True }, name='editor_upload_image' ),
    re_path( r'^upload_link/%s' % _upload_args, editor.upload_file, { 'link': True }, name='editor_upload_link' ),

    ]

root_patterns = [

    # DevOps pages

    re_path( r'^dashboard', devops.dashboard, name='ops_dashboard' ),
    re_path( r'^logging', devops.logging, name='ops_logging' ),
    re_path( r'^sysflags', devops.system_flags, name='ops_system_flags' ),
    re_path( r'^siteflags', devops.sandbox_flags, name='ops_sandbox_flags' ),

    # Pages to help debugging

    re_path( r'^urls$', testing.mptest_urls, name='mptest_urls'),
    re_path( r'^info$', testing.mptest_info, name='mptest_info'),
    re_path( r'^ajax_api$', testing.mptest_ajax_endpoint, name='mptest_ajax_endpoint'),

    # Test pages to exercise code

    re_path( r'^test/calls', testing.mptest_helper_calls, name='mptest_helper_calls' ),
    re_path( r'^test/forms', testing.mptest_helper_forms, name='mptest_helper_forms' ),

    re_path( r'^test/exc_view', testing.mptest_exc_view, name='mptest_exc_view' ),
    re_path( r'^test/exc_404', testing.mptest_exc_404, name='mptest_exc_404' ),
    re_path( r'^test/pop', testing.mptest_popup, name='mptest_popup' ),
    re_path( r'^test/csrf', testing.mptest_csrf, name='mptest_csrf' ),
    re_path( r'^test/logging/(?P<log>[\w-]+)', testing.mptest_logging, name='mptest_logging' ),
    re_path( r'^test/email/(?P<num>[0-9]+)', testing.mptest_email, name='mptest_email' ),
    re_path( r'^test/uwsgi/(?P<command>[A-Z]+)', testing.mptest_uwsgi, name='mptest_uwsgi' ),

    re_path( r'^test/task/(?P<num>[0-9]+)$', testing.mptest_task, name='mptest_task' ),
    re_path( r'^test/task/(?P<num>[0-9]+)/(?P<p>[A-Z0-9]+)$', testing.mptest_task, name='mptest_task' ),
    re_path( r'^test/task/(?P<num>[0-9]+)/(?P<p>[A-Z0-9]+)/(?P<c>[\w]+)', testing.mptest_task, name='mptest_task' ),
    re_path( r'^test/job/(?P<tasks>[0-9]+)/(?P<p>[A-Z0-9]+)$', testing.mptest_job, name='mptest_job' ),
    re_path( r'^test/job/(?P<depth>[0-9]+)/(?P<tasks>[0-9]+)/(?P<jobs>[0-9]+)', testing.mptest_job, name='mptest_job' ),

    ]
if settings.MP_DEVWEB and not settings.MP_TESTING:
    from django.urls import include
    import debug_toolbar
    root_patterns += [
        # Add the toolbar's path to the no-login urls
        re_path( r'^__debug__/', include( debug_toolbar.urls ) ),
        # Allow access to local work folder
        re_path( r'^dev_workfiles/(?P<workpath>.+)$', testing.dev_workfiles ),
        # Dev only test screens
        re_path( r'^local_cache$', testing.mptest_local_cache, name='mptest_local_cache' ),
        ]
