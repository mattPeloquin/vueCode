#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Catalog context processors
"""

from .utils import free_pa_content


def catalog( request ):
    if request.is_healthcheck or request.is_bad:
        return {}

    context = {
        'access_free_items': lambda: free_pa_content( request.sandbox.pk ),
        }

    return context
