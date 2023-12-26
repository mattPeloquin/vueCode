#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Key GA admin report that breaks down user vs. item usage
    at both summary (top collections) and detailed (per-item) levels.
"""

from mpframework.common.tasks import mp_async
from mpframework.common.utils import tz
from mpframework.common.utils.strings import wb
from mpframework.common.api import respond_api_call
from mpextend.product.account.group import group_admin_view

from ..users.summary import u2_report
from .._utils.user_rows import user_rows_factory
from .._utils.content_rollup import top_usercontent_headers
from .._utils.content_rollup import top_usercontent_add
from .._utils.content_rollup import top_usercontent_totals
from ._shared import start_ga_report
from .summary import user_report1


_report_top = {
    "Collection":   lambda ui:  ui['name'],
    }
_report_item = {
    "Content":      lambda ui:  ui['name'],
    "Collection":   lambda ui:  ui['top_name'],
    "Type":         lambda ui:  ui['portal_type'] or ui['ctype'],
    }
_report = {
    "Completed":      lambda u,ui:  wb( ui['is_complete'] ),
    "License":        lambda u,ui:  u.apas.get( ui['apa_id'] ) or "",
    "Last use":       lambda u,ui:  tz( ui['last_used'] ).date(),
    "Completion":     lambda u,ui:  tz( ui['completed'] ).date() if ui['completed'] else "",
    "Start":          lambda u,ui:  tz( ui['hist_created'] ).date(),
    "Approx hours":   lambda u,ui:  ui['minutes_used'] // 60,
    "Approx minutes": lambda u,ui:  ui['minutes_used'],
    "Total uses":     lambda u,ui:  ui['uses'],
    }

@group_admin_view
def ga_content_top_csv( request, account ):
    return _content_csv( request, account, detailed=False )

@group_admin_view
def ga_content_csv( request, account ):
    return _content_csv( request, account, detailed=True )

def _content_csv( request, account, detailed ):
    def handler( _get ):
        header = list( _report_item ) if detailed else list( _report_top )
        header += list( user_report1 )
        header += list( _report )
        header += () if detailed else top_usercontent_headers()
        header += list( u2_report )
        return start_ga_report( request, account, header, _content_rows_fn, detailed=detailed )

    return respond_api_call( request, handler, methods=['GET'] )

def _content_rows( user, data, writer ):

    # For detailed reports, write every user item row
    if data['detailed']:
        for ui in user.useritems:
            row_items = [ fn( ui ) for fn in _report_item.values() ]
            row_items += [ fn( user ) for fn in user_report1.values() ]
            row_items += [ fn( user, ui ) for fn in _report.values() ]
            row_items += [ fn( user ) for fn in u2_report.values() ]
            writer.writerow( row_items )

    # For summary reports, one row for each top item, with user content
    else:
        totals = top_usercontent_totals( user )
        for top in user.usertops:
            row_items = [ fn( top ) for fn in _report_top.values() ]
            row_items += [ fn( user ) for fn in user_report1.values() ]
            row_items += [ fn( user, top ) for fn in _report.values() ]
            row_items += top_usercontent_add( top, totals )
            row_items += [ fn( user ) for fn in u2_report.values() ]
            writer.writerow( row_items )

_user_rows_fn = user_rows_factory( _content_rows )

@mp_async
def _content_rows_fn( **kwargs ):
    return _user_rows_fn( **kwargs )
