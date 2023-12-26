#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Support global coupon redemption (outside access popup)
"""
from django.template.response import TemplateResponse

from mpframework.common.view import login_required
from mpextend.product.catalog.models import PA


@login_required
def profile_coupon( request ):
    """
    Send purchase SKUs to coupon page so access dialog can be
    shown if needed.
    """
    return TemplateResponse( request, 'user/profile/coupon.html', {
                'portal_skus': PA.objects.get_purchase_pas( request.sandbox.pk ),
                })
