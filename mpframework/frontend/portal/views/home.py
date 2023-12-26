#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Support for configurable site root, i.e., "sandbox1.vueocity.com"
"""
from django.http import HttpResponseRedirect
from django.http import HttpResponsePermanentRedirect
from django.urls import reverse

from mpframework.common import log


def site_home( request, **kwargs ):
    """
    Redirect the root URL of the site based on sandbox settings.
    Don't use root for direct hosting, since there are various naming conventions
    tied to portal and catalog, and makes SEO cleaner.
    """
    sandbox = request.sandbox
    assert sandbox

    # Special case the root portal
    if sandbox.is_root:
        return HttpResponseRedirect(
                    reverse('root_admin:tenant_provider_changelist') )

    home_url = reverse('portal_view')

    # If a scheme shift was requested, incorporate it into redirect
    scheme_change = getattr( request, 'mpscheme', None )
    if scheme_change:
        home_url = '{}://{}{}'.format( scheme_change, request.host, home_url )
        log.info3("Home redirect, scheme: %s -> %s", sandbox, home_url )

    return HttpResponsePermanentRedirect( home_url )
