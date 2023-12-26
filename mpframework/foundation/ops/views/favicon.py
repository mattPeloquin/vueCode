#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Root favicon response
"""
from django.conf import settings
from django.http import HttpResponse

from mpframework.common.deploy.nginx import accel_redirect_public


def sandbox_favicon( request ):
    """
    Respond to the favicon.ico root request per sandbox.

    Ideally all favicon behavior would be driven from the style <link>
    values; but some browsers (Chrome) seem to respond only to
    favicon.ico in some scenarios.
    """
    if settings.MP_CLOUD:
        return accel_redirect_public( request.sandbox.icon.url )

    return HttpResponse()