#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    User group account administration
"""

from mpframework.common.tasks import mp_async
from mpframework.common.api import respond_api_call
from mpextend.product.account.group import group_admin_view

from ..users.summary import u2_report
from .._utils.user_content_summary import content_headers
from .._utils.user_content_summary import content_row_items
from .._utils.user_rows import user_rows_factory
from ._shared import start_ga_report


user_report1 = {
    'Email':          lambda u:  u.email,
    'First name':     lambda u:  u.first_name,
    'Last name':      lambda u:  u.last_name,
    }

@group_admin_view
def ga_summary_csv( request, account ):
    """
    Allow admins to export their users
    FUTURE - combine account csv into one report? Or include rollups in summary
    """
    def handler( _get ):
        header = list( user_report1 ) + content_headers() + list( u2_report )
        return start_ga_report( request, account, header, _summary_rows_fn )
    return respond_api_call( request, handler, methods=['GET'] )

def _summary_row( user, data, writer ):
    row_items = [ fn(user) for fn in user_report1.values() ]
    row_items += content_row_items( user )
    row_items += [ fn(user) for fn in u2_report.values() ]
    writer.writerow( row_items )

_user_rows_fn = user_rows_factory( _summary_row )

@mp_async
def _summary_rows_fn( **kwargs ):
    return _user_rows_fn( **kwargs )
