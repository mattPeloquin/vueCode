#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    User group account administration
"""

from mpframework.common.tasks import mp_async
from mpframework.common.utils.strings import wb
from mpframework.common.api import respond_api_call
from mpextend.product.account.group import group_admin_view

from ..users.summary import u2_report
from .._utils.user_rows import user_rows_factory
from ._shared import start_ga_report


report = {
    'Email':          lambda u, apa:  u.email,
    'First name':     lambda u, apa:  u.first_name,
    'Last name':      lambda u, apa:  u.last_name,
    'License':        lambda u, apa:  apa.pa.description,
    'Type':           lambda u, apa:  apa.purchase_type_lookup,
    'Current price':  lambda u, apa:  apa.access_price,
    'Subscription':   lambda u, apa:  wb( apa.is_subscription ),
    'Renewals':       lambda u, apa:  apa.renewals,
    'Coupon':         lambda u, apa:  apa.coupon,
    'Period start':   lambda u, apa:  apa.period_start_date,
    'Period end':     lambda u, apa:  apa.period_end_date,
    }

@group_admin_view
def ga_purchases_csv( request, account ):
    def handler( _get ):
        if not account:
            return
        header = list( report )

        # Do one-time get of all apa and user-relation information
        apas = list( account.get_apas() )
        apa_users = {}
        for apa in apas:
            apa_users.update({ apa.id: apa.user_ids })
        data = {
            'apas': apas,
            'apa_users': apa_users,
             }
        return start_ga_report( request, account, header, _purchase_rows_fn, data )

    return respond_api_call( request, handler, methods=['GET'] )

def _purchase_rows( user, data, writer ):
    apas = data['apas']
    apa_users = data['apa_users']
    for apa in apas:
        if user.pk in apa_users[ apa.pk ]:
            row_items = [ fn(user, apa) for fn in report.values() ]
            row_items += [ fn(user) for fn in u2_report.values() ]
            writer.writerow( row_items )

_user_rows_fn = user_rows_factory( _purchase_rows )

@mp_async
def _purchase_rows_fn( **kwargs ):
    return _user_rows_fn( **kwargs )
