#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Ops extensions for templat context shared across apps
"""
from django.conf import settings


def common( request ):
    return {
        'MP_EXTERNAL': settings.MP_EXTERNAL,
        }
