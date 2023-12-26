#--- Vueocity Platform, Copyright 2021 Vueocity, LLC
"""
    Portal bootstrap
"""

from django.http import Http404

from mpframework.common import log
from mpframework.common.api import respond_api_call

from mpframework.foundation.tenant.models.sandbox import Sandbox


def domain_check( request, subdomain ):
    """
    See if the requested domain is valid and available
    If not, raise a 404
    """
    def handler( values ):
        log.info2("ONBOARD domain check: %s -> %s", request.mpipname, subdomain )

        ok = Sandbox.objects.subdomain_ok( subdomain )

        if not ok:
            log.info2("Domain rejected: %s -> %s", request.mpipname, subdomain )
            raise Http404

    return respond_api_call( request, handler, methods=['GET'] )
