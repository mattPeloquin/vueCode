#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Support for Content Security Policy (CSP)
"""
from functools import wraps
from django.conf import settings


CSP_IFRAME_ANY = 'any'
CSP_IFRAME_SITE = 'site'


"""
Mark view functions as ok for display in iframe
"""

def iframe_allow_any( view_func ):
    def wrapped_view( request, *args, **kwargs ):
        request.iframe_allow = CSP_IFRAME_ANY
        return view_func( request, *args, **kwargs )
    return wraps( view_func )( wrapped_view )

def iframe_allow_site( view_func ):
    def wrapped_view( request, *args, **kwargs ):
        request.iframe_allow = CSP_IFRAME_SITE
        return view_func( request, *args, **kwargs )
    return wraps( view_func )( wrapped_view )
