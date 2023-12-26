#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Sitebuilder catalog links
"""
from django.urls import reverse
from django.template.response import TemplateResponse

from mpframework.common.view import staff_required
from mpextend.product.catalog.models import PA
from mpextend.product.catalog.models import Coupon


@staff_required
def sku_links( request ):
    pas = []
    for pa in PA.objects.filter( request=request ):
        pa_dict = pa.dict
        pa_dict.update({
                'login_url': reverse('login_sku', kwargs={ 'sku': pa.sku }),
                })
        pas.append( pa_dict )
    request.is_page_staff = True
    return TemplateResponse( request, 'sitebuilder/easylinks/sku_links.html', {
                'pas': pas,
                })

@staff_required
def coupon_links( request ):
    coupons = []
    for coupon in Coupon.objects.filter( request=request, enabled=True ):
        cd = coupon.dict
        cd.update({
                'login_url': reverse('login_coupon', kwargs={ 'coupon_slug': coupon.code }),
                })
        coupons.append( cd )
    request.is_page_staff = True
    return TemplateResponse( request, 'sitebuilder/easylinks/coupon_links.html', {
                'coupons': coupons,
                })
