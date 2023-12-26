#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Template context shared across apps
"""
import operator
from functools import reduce
from django.conf import settings
from django.urls import reverse
from django.utils.functional import lazy

from mpframework.common import log
from mpframework.common import sys_options
from mpframework.common.utils import join_urls
from mpframework.common.compat import compat_static
from mpframework.common.logging.utils import db_queries


def common( request ):
    """
    Do not pass entire request or settings to templates; force interfaces
    for system context that will be used in templates
    """
    if request.is_bad:
        return {}

    # Start with the offline processing
    context = settings.TEMPLATE_OFFLINE_CONTEXT

    # HACK - Fixup static URL serving based on compatibility
    if request.user and request.user.use_compat_urls:
        static_url = compat_static( context['static_url'] )
        context.update({
            'static_url_orig': settings.MP_ROOT_URLS['URL_STATIC'],
            'static_url_new': settings.MP_ROOT_URLS['URL_STATIC_COMP'],
            'static_url': static_url,
            'static_url_resource': join_urls( static_url, 'mpf-root' ),
            })

    context.update({

        # Markers for identifying the call
        'request_ip': request.ip,
        'request_mpipname': request.mpipname,
        'request_mpremote': request.mpremote,
        'request_info': getattr( request, 'mpinfo', {} ),

        # Pass along key page types to context - for UI behavior, NOT security
        'is_portal': request.is_portal,
        'is_page_admin': request.is_page_admin,
        'is_page_staff': request.is_page_staff,
        'is_popup': request.is_popup,
        'is_popup_close': request.is_popup_close,
        'page_id': _page_id( request ),
        'referrer': request.referrer,

        # Current portal root default -- may be overridden by specialized portal views
        'url_portal': reverse('portal_view'),

        # Other URL helpers; normally prefer {% url %} tag, these are special cases
        'url_current': request.path,
        'url_no_param': request.path.rstrip('_/1234567890'),
        'url_login': reverse('login'),
        'url_public': settings.MP_URL_PUBLIC,
        'url_deeplinker': settings.MP_URL_NAV_DEEPLINK,

        # Allow configuration of CSRF cookie
        'csrf_cookie_name': settings.CSRF_COOKIE_NAME,

        # Values for various client timeouts
        'timeout_error': settings.MP_TUNING['CLIENT_ERROR_TIMEOUT'],
        'timeout_idle': settings.MP_TUNING['CLIENT_IDLE_WAIT'],
        'timeout_ping': sys_options.client_ping(),
        'browser_cache_age': settings.MP_CACHE_AGE['BROWSER'],

        'log_info_level': log.info_on(),
        'log_debug_level': log.debug_on(),
        })

    """
    Admin base template default
    The template_add_change_base extends tag variable controls whether admin pages
    are loaded into Root or Staff/Sandbox frames. It is set here because there
    isn't a catch-all hook in the admin for setting extra context.
    """
    add_change_base = 'admin/base.html'
    if request.mppath.startswith( settings.MP_URL_STAFF_ADMIN ):
        add_change_base = 'admin/_page.html'
    context['template_add_change_base'] = add_change_base

    # Add marker for supporting web test success checks
    if settings.MP_TESTING_UNIT:
        context['test_success_inject'] = request.mptest['inject_text']

    return context

def _page_id( request ):
    """
    Create unique slug/id for url that can be used with CSS to target
    particular URLs in both portal and admin.
    For non-portal, do NOT include ID values from URL, '_' default values,
    or MPF prefixes.
    """
    segs = request.mppathsegs
    if not request.is_portal:
        segs = [ seg for seg in request.mppathsegs if (
                    not seg.isdigit() and seg not in ['bh', 'ad', '_'] ) ]
    return '-'.join( segs )

def mpdebug( request ):
    """
    Provide debug values in the templates, including duplicating SQL
    behavior from Django debug context processor since it assumes remote_addr
    checks for internal IP which doesn't work for prod-mpd.
    This will not be registered if DEBUG is false, so templates must ensure
    graceful failure if values are not present
    """
    rv = {
        'no_robots': True,
        }
    if request.is_lite:
        return rv

    if request.ip not in settings.INTERNAL_IPS:
        log.warning("SUSPECT DEV IP: %s -> %s", request.mpipname, request.uri )
        rv.update({
            'debug': False,
            'dev_page_tools': False,
            })
    else:
        # For SQL query list, use a lazy reference that computes connection.queries on access,
        # to ensure it contains queries triggered after this function runs.
        queries = lazy( db_queries, list )
        rv.update({
            'debug': True,
            'dev_page_tools': request.sandbox.flag('DEV_show_page_tools'),

            # Make settings available for dispaly
            'debug_settings': settings,
            'debug_db_names': [ "-".join([ n, db.get('NAME') ]) for n, db in settings.DATABASES.items() ],
            'debug_cache_names': [ "-".join([ n, c.get('BACKEND') ]) for n, c in settings.CACHES.items() ],

            # Get DB timings from DB connection
            'sql_queries': queries,
            'db_time': reduce( operator.add, [ float(q.get('time')) for q in queries() ], 0.0 ),
            })

    return rv
