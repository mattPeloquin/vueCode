#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    User-specific context processors
"""
from django.urls import reverse


def user( request ):
    if request.is_lite or request.is_bad:
        return {}

    context = {
        'user': request.user,
        }

    return context
