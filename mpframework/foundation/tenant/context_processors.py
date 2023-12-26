#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Tenant-specific context processors
"""
from django.conf import settings
from django.urls import reverse

from mpframework.common import sys_options
from mpframework.common.compat import compat_static
from mpframework.common.utils.request import edge_public_url


def tenant( request ):
    if request.is_healthcheck or request.is_api:
        return {}
    sandbox = request.sandbox
    use_compat_urls = request.user.use_compat_urls

    context = {
        'site': sandbox,

        # Setup url to sandbox CSS through edge server
        'url_sandbox_css': lambda: _sandbox_css_url( request ),

        # Adjust compatibility URLs if needed
        'media_url': lambda: compat_static( sandbox.media_url, use_compat_urls ),
        'content_media_url': lambda: compat_static(
                sandbox.provider.content_media_url, use_compat_urls ),

        # System options and flags
        'root_google_gtm': sys_options.root().policy.get( 'google', '' ),
        'site_flags': lambda: _site_flags( sandbox ),
        }
    return context

def _sandbox_css_url( request ):
    """
    Sandbox CSS is served via separate URL for caching in browser and CDN.
    Url cache key uses sandbox version, request skin hash, code rev,
    and dev workflow to ensure CSS represents current in all dimensions.
    No CORS hashing on host is needed because it is a normal HTTP GET.
    """
    cache_url = '{}{}{}{}'.format( settings.MP_CODE_CURRENT,
                request.sandbox.cache_group_version,
                request.skin.cache_template_key( request.user ),
                'D' if request.user.workflow_dev else '' )
    url = reverse( 'edge_sandbox_css', kwargs={
                'no_host_id': request.sandbox.pk,
                'cache_url': cache_url,
                })
    if settings.MP_CLOUD:
        url = edge_public_url( request, url )
    return url

def _site_flags( sandbox ):
    """
    Make dict of all current system flags and any site overrides
    for easy use in templates.
    """
    rv = {}
    for name in sys_options.flags():
        rv[ name ] = sandbox.flag( name )
    return rv
