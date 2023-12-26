#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Portal context, sets up bootsrapping context
"""
from django.conf import settings
from django.urls import reverse

from mpframework.common.utils.request import edge_public_url
from mpframework.common.utils.request import edge_version
from mpframework.user.mpuser.cache import user_timewin_hash
from mpframework.content.mpcontent.cache import content_timewin_hash


def portal( request ):
    if request.is_lite or request.is_api or request.is_bad:
        return {}
    return {
        'url_bootstrap_delta': lambda: _embed_bootstrap( request ),
        'url_bootstrap_content': lambda: _content_bootstrap( request ),
        'url_bootstrap_user': lambda: _user_bootstrap( request ),
        'url_bootstrap_nocache': lambda: _nocache_bootstrap( request ),
        'is_portal_content': request.is_portal_content,
        'dev_keep_ko_bindings': request.sandbox.flag('DEV_keep_ko_bindings'),
        }

def _embed_bootstrap( request ):
    """
    Support the option of moving embedded content into a line
    """
    if( request.sandbox.options['bootstrap.embed_in_link'] ):
        return reverse('bootstrap_delta')

def _content_bootstrap( request ):
    """
    Return content bootstrap URL cacheable in browser and edge server
    """
    if( not request.sandbox.options['bootstrap.content_data_in_page'] ):
        version = content_timewin_hash( request )
        version = edge_version( request, version )
        url = reverse( 'edge_bootstrap_content', kwargs={
                    'no_host_id': request.sandbox.pk,
                    'cache_url': version,
                    })
        if settings.MP_CLOUD:
            url = edge_public_url( request, url )
        return url

def _user_bootstrap( request ):
    """
    Return URL for user bootstrap if it should be called
    """
    if( request.user.is_ready() and
            not request.sandbox.options['bootstrap.user_data_in_page'] ):
        return reverse( 'bootstrap_user', kwargs={
                    'cache_url': user_timewin_hash( request ),
                    })

def _nocache_bootstrap( request ):
    """
    Currently only call the nocache bootstrap for user delta data
    """
    if( request.user.is_ready() and
            not request.sandbox.options['bootstrap.nocache_data_in_page'] ):
        return reverse('bootstrap_nocache')
