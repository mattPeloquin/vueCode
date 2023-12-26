#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    LMS API Views
"""
from mpframework.common import log
from mpframework.common.utils import json_dump
from mpframework.common.api import api_get_id
from mpframework.common.api import respond_api_call
from mpframework.common.view import staff_required
from mpframework.foundation.ops.csp import iframe_allow_any
from mpextend.user.usercontent.api import user_item

from ..mpcontent.models import LmsItem


# FUTURE SECURE -- possible to setup CSRF correctly for CF redirects?
from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
@iframe_allow_any
def cflms_origin_user_items( request, no_host_id ):
    """
    Calling user_item when passing through a CF Origin URL
    when LMS content run an IFrame pointing at CF
    """
    return user_item( request )


@staff_required
def package_metrics( request ):
    """
    For an LMS item, provide a JSON dictionary of all packages related
    to the item with counts of students that are linked to each
    """
    def handler( payload ):
        id = api_get_id( payload.get('lms_id') )
        lms = LmsItem.objects.get( request=request, id=id )
        log.debug("API package_metrics: %s -> %s", request.user, lms)

        metrics = {}
        for package in lms.package_root.all_packages:
            metrics[ "id" + str(package.pk) + "-" + str(package) ] = package.user_count
        log.debug_values(metrics)

        return { 'package_metrics_dict': json_dump( metrics ) }

    return respond_api_call( request, handler, methods=['GET'] )
