#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Content CSV reports
    Optimized reporting focused on usage of collections and items
"""
from django.conf import settings

from mpframework.common import log
from mpframework.common.tasks import mp_async
from mpframework.common.utils import tz
from mpframework.common.utils.strings import wb
from mpframework.common.view import staff_required
from mpframework.common.api import respond_api_call

from ..jobs import SandboxReportJob
from .._utils.user_block import define_user_blocks
from .._utils.user_rows import user_rows_factory
from .._utils.content_rollup import top_usercontent_headers
from .._utils.content_rollup import top_usercontent_add
from .._utils.content_rollup import top_usercontent_totals
from .summary import u1_report
from .summary import u2_report


uc_report_top = {
    "Collection":      lambda ui:  ui['name'],
    "License tag":     lambda ui:  ui['tag'],
    "Internal tag":    lambda ui:  ui['internal'],
    }
uc_report_item = {
    "Content":         lambda ui:  ui['name'],
    "License tag":     lambda ui:  ui['tag'],
    "Internal tag":    lambda ui:  ui['internal'],
    "Collection":      lambda ui:  ui['top_name'],
    "Size":            lambda ui:  ui['size'] if ui['size'] else "",
    "Points":          lambda ui:  ui['points'] if ui['points'] else "",
    }
uc_report = {
    "Portal type":     lambda u,ui,a:  ui['portal_type'],
    "Content type":    lambda u,ui,a:  ui['ctype'],
    "Completed":       lambda u,ui,a:  wb( ui['is_complete'] ),
    "Last use":        lambda u,ui,a:  tz( ui['last_used'] ).date(),
    "Start":           lambda u,ui,a:  tz( ui['hist_created'] ).date(),
    "Completion":      lambda u,ui,a:  tz( ui['completed'] ).date() if
                                              ui['completed'] else "",
    "Total uses":      lambda u,ui,a:  ui['uses'],
    "Approx minutes":  lambda u,ui,a:  ui['minutes_used'],
    "Approx hours":    lambda u,ui,a:  ui['minutes_used'] // 60,
    "Feedback":        lambda u,ui,a:  ui['feedback'] or "",
    "Last license":    lambda u,ui,a:  a or "",
    "Active":          lambda u,ui,a:  wb( a.is_active() ) if a else "",
    "Purchase type":   lambda u,ui,a:  a.purchase_type_lookup if a else "",
    "Pricing option":  lambda u,ui,a:  a.pa if a else "",
    "Coupon":          lambda u,ui,a:  a.coupon if a else "",
    "Trial":           lambda u,ui,a:  wb( a.is_trial ) if a else "",
    "Price":           lambda u,ui,a:  a.access_price if a and a.access_price else "",
    "Subscription":    lambda u,ui,a:  a.is_subscription if a else "",
    "Last use time":   lambda u,ui,a:  tz( ui['last_used'] ).time(),
    "Start time":      lambda u,ui,a:  tz( ui['hist_created'] ).time(),
    }
if settings.DEBUG:
    uc_report['CU ID'] = lambda u,ui,a: ui['id']
    uc_report['User ID'] = lambda u,ui,a: u.pk


@staff_required
def users_content_top_csv( request, start=None ):
    return users_content_csv( request, start, detailed=False )

@staff_required
def users_content_csv( request, start=None, detailed=True ):
    """
    Content usage report broken down by each user use
    """
    def handler( _get ):
        log.info("START USER CONTENT REPORT %s: %s -> %s, %s", request.mptiming,
                                                request.mpname, detailed, start)
        name = "User" + ( "CollectionUsage" if not detailed else "ItemUsage" )
        data = {
            'name': name,
            'start': start,
            'detailed': detailed,
             }

        shared_cols = list( u1_report ) + list( uc_report ) + list( u2_report )
        if detailed:
            header = list( uc_report_item ) + shared_cols
        else:
            header = list( uc_report_top ) + top_usercontent_headers() + shared_cols

        job = SandboxReportJob( name, request, header, _user_content_rows_fn, data=data )

        log.debug("Creating user blocks for content report: %s", job)
        blocks = define_user_blocks( job.sandbox_id,
                    settings.MP_REPORT['USER_BLOCK_SIZE'], start )
        for user_ids in blocks:
            job.add_report_task( user_ids=user_ids )

        job.start()

        return { 'report': name, 'start': start, 'blocks': len(blocks) }
    return respond_api_call( request, handler, methods=['GET'] )

def _content_rows( user, data, writer ):

    def shared_cols( ui ):
        row_items = [ fn( user ) for fn in u1_report.values() ]
        row_items += [ fn( user, ui, user.apas.get( ui['apa_id'] ) ) for
                            fn in uc_report.values() ]
        row_items += [ fn( user ) for fn in u2_report.values() ]
        return row_items

    # For detailed reports, write every user item row
    if data['detailed']:
        for ui in user.useritems:
            row_items = [ fn( ui ) for fn in uc_report_item.values() ]
            row_items += shared_cols( ui )
            writer.writerow( row_items )

    # For summary reports, one row for each top item, with rollups
    else:
        totals = top_usercontent_totals( user )
        for top in user.usertops:
            row_items = [ fn( top ) for fn in uc_report_top.values() ]
            row_items += top_usercontent_add( top, totals )
            row_items += shared_cols( top )
            writer.writerow( row_items )

_user_rows_fn = user_rows_factory( _content_rows )

@mp_async
def _user_content_rows_fn( **kwargs ):
    return _user_rows_fn( **kwargs )
