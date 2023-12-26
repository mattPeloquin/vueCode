#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared compatibility code not related to delivery
"""
from django.conf import settings


"""-------------------------------------------------------------------
    Compatibility for public URLs
    HACK - Dynamic change public/static urls to compatibility ones
    Done as a replacement AFTER URL is created, since this rare adjustment
    would impact more code if considered during creation of every public URL.
"""

def compat_public( url, condition=True ):
    if condition:
        url = url.replace( settings.MP_ROOT_URLS['URL_PUBLIC'],
                           settings.MP_ROOT_URLS['URL_PUBLIC_COMP'] )
    return url

def compat_static( url, condition=True ):
    if condition:
        url = url.replace( settings.MP_ROOT_URLS['URL_STATIC'],
                           settings.MP_ROOT_URLS['URL_STATIC_COMP'] )
    return url
