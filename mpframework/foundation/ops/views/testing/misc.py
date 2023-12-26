#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Various test views
"""
from django.conf import settings
from django.http import StreamingHttpResponse
from django.template.response import TemplateResponse

from mpframework.common import log
from mpframework.common.view import root_only
from mpframework.common.api import api_get_id
from mpframework.common.api import respond_api_call
from mpframework.common.deploy.debug import get_settings_dict
from mpframework.common.utils.http import get_url_list
from mpframework.common.utils.strings import safe_unicode
from mpframework.common.deploy.paths import work_path


@root_only
def mptest_ajax_endpoint( request ):
    """
    Dummy endpoint to test CORS in production
    """
    def handler( payload ):
        test_value = api_get_id( payload.get('test_value') )
        user = request.user
        log.info("TEST AJAX CALL: %s", test_value)

        if user.is_authenticated:
            return test_value

    return respond_api_call( request, handler )

@root_only
def mptest_urls( request ):

    # NGINX prefixes; use values used for config file
    from ...management.commands.config_framework import nginx_context
    n = nginx_context()
    nginx_urls = [
        "Main uWsgi: " + n.get('URL_NGINX_MAIN'),
        "Public uWsgi: " + n.get('URL_NGINX_PUBLIC'),
        "Admin uWsgi: " + n.get('URL_NGINX_ADMIN'),
        "Health: " + settings.MP_HEALTHCHECK_URL,
        "Root pass: " + n.get('URL_NGINX_ROOT_PASS'),
        "Nginx public direct: " + settings.MP_URL_PUBLIC_DIRECT,
        "Nginx protected pass: " + settings.MP_URL_PROTECTED_PASS + " (ending in: " +
            n.get('PROTECTED_NGINX_PASS_TYPES') + ")",
        ]

    # Create simple display of all valid URL regex in the system
    urls = get_url_list()
    root_urls = [ url for url in urls if url.startswith( settings.MP_URL_ROOTSTAFF ) ]
    boh_urls = [ url for url in urls if url.startswith( settings.MP_URL_BOH ) ]
    ft_urls = [ url for url in urls if url.startswith( settings.MP_URL_FT ) ]
    main_urls = list( set(urls) - set(boh_urls) - set(ft_urls) - set(root_urls) )
    main_urls.sort()
    admin_urls = [ url for url in boh_urls if url.startswith( settings.MP_URL_STAFF_ADMIN ) ]
    external_urls = [ url for url in boh_urls if url.startswith( settings.MP_URL_EXTERNAL ) ]
    boh_urls = list( set(boh_urls) - set(admin_urls) - set(external_urls) )
    boh_urls.sort()

    return TemplateResponse( request, 'root/test/urls.html', {
                'nginx_urls': nginx_urls,
                'main_urls': main_urls,
                'boh_urls': boh_urls,
                'ft_urls': ft_urls,
                'admin_urls': admin_urls,
                'root_urls': root_urls,
                'external_urls': external_urls,
                })

@root_only
def mptest_info( request ):
    """
    Display internal information not present in the options
    """
    # Create display dictionary out of request
    request_dict = {}
    for key, value in sorted( request.META.items() ):
        request_dict[key] = value

    return TemplateResponse( request, 'root/test/info.html', {
                    'request_dict': request_dict,
                    'mpf_settings': get_settings_dict(),
                    })

@root_only
def mptest_local_cache( request ):
    """
    DEV ONLY
    Display local in-mem cache
    """
    from django.core.cache import caches

    # DEV HACK - reach into cache local thread to get LocMemCache dict,
    # which is shared across all caches. Just grab local_small,
    # which should have dict with all items
    cache_dict = caches['local_small']._cache
    return TemplateResponse( request, 'root/test/local_cache.html', {
                'cache_items': [ { 'key': key, 'value': safe_unicode(value) }
                                    for key, value in cache_dict.items() ],
                })

def dev_workfiles( request, *args, **kwargs ):
    """
    DEV ONLY
    Provide access to files in work folder when running dev server
    """
    path = kwargs.get('workpath')
    path = work_path( path )
    log.debug("LOCAL WORK PATH FILE REQUEST: %s", path)
    return StreamingHttpResponse(
                _localfile_stream_generator(path),
                content_type='text/plain'
                )

def _localfile_stream_generator( path, block_size=8192 ):
    with open( path, 'r' ) as work_file:
        for line in work_file:
            yield line
