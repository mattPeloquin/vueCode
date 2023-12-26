#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared testing code
"""
from django.conf import settings


# For some test code it is easier to maintain URLs rather than
# use Django reverse(). These utils provide dynamic fixup
# where needed for differnet URL configurations

def bh( url ):
    return _prefix_url( settings.MP_URL_BOH, url )

def ft( url ):
    return _prefix_url( settings.MP_URL_FT, url )

def _prefix_url( prefix, url ):
    if prefix:
        if url.startswith('/'):
            prefix = '/{}'.format( prefix )
        else:
            prefix = '{}/'.format( prefix )
        url = prefix + url
    return url
