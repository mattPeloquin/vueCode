#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Dashboard view support
"""
from django.conf import settings
from django.template.response import TemplateResponse

from mpframework.common import sys_options
from mpframework.common.utils import now
from mpframework.common.utils import timedelta_past
from mpframework.common.view import staff_required
from mpextend.user.usercontent.models import UserItem


@staff_required
def user_dashboard( request ):
    """
    Main staff dashboard view
    """
    sandbox = request.sandbox
    _now = now( sandbox.timezone )
    metrics = {}

    def active_users_since( start ):
        return sandbox.users.mpusing('read_replica')\
                .filter( tracking__last_update__gte=start )\
                .count()
    metrics['users'] = time_metrics_since( _now, active_users_since )

    def new_users_since( start ):
        return sandbox.users.mpusing('read_replica')\
                .filter( hist_created__gte=start )\
                .count()
    metrics['new'] = time_metrics_since( _now, new_users_since )

    def usage_since( start ):
        return UserItem.objects.mpusing('read_replica')\
                .filter( sandbox=sandbox, last_used__gte=start, top_tree__isnull=False )\
                .count()
    metrics['usage'] = time_metrics_since( _now, usage_since )

    request.is_page_staff = True
    return TemplateResponse( request, 'user/dashboard.html', {
                'root_google_maps': sys_options.root().policy.get( 'google_maps', '' ),
                'user_report_max': settings.MP_TRACKING['MAX_RECENT'],
                'users_total': sandbox.users.mpusing('read_replica').count(),
                'metrics': metrics,
                })

def time_metrics_since( _now, qs_fn ):
    return {
        'hour': qs_fn( timedelta_past( _now, hours=1 ) ),
        'day': qs_fn( _now.replace( hour=0, minute=0 ) ),
        'week': qs_fn( timedelta_past( _now, weeks=1 ) ),
        'weeks': qs_fn( timedelta_past( _now, weeks=4 ) ),
        'month': qs_fn( _now.replace( day=1, hour=0, minute=0 ) ),
       }

