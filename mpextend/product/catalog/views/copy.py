#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Copy all catalog information to new sandbox
"""

from django.template.response import TemplateResponse

from mpframework.common import log
from mpframework.common.view import staff_required

from mpframework.foundation.tenant.models.sandbox import Sandbox

from ..models.pa import PA
from ..models.coupon import Coupon


@staff_required( owner=True )
def copy_product( request ):
    sandbox = request.sandbox

    # Text blobs that describe output
    output = []

    if 'POST' == request.method:
        dest_name = request.POST.get('sandbox_name')
        try:
            dest_sandbox = Sandbox.objects.get( provider_id=sandbox._provider_id,
                        name=dest_name )

            if sandbox == dest_sandbox or sandbox.provider != dest_sandbox.provider:
                log.error("Invalid sandbox copy attempt: %s -> %s", sandbox, dest_sandbox)
                return

            pas = PA.objects.clone_sandbox_objects( sandbox, dest_sandbox )
            coupons = Coupon.objects.clone_sandbox_objects( sandbox, dest_sandbox )

            for item in pas + coupons:
                output.append( u"Created: {}".format( item ) )

        except Sandbox.DoesNotExist:
            output.append("There is no destination sandbox with that name")

        except Exception:
            log.exception("Problem with copy products view")
            output.append("This copy cannot be completed")

    request.method = 'GET'

    return TemplateResponse( request, 'catalog/copy_sandbox_product.html', {
                 'output': output,
                 })
