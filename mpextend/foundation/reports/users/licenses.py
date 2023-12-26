#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    User license report
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
from .summary import u1_report
from .summary import u2_report


pu_report = {
    'License':        lambda a, u:  a.name,
    'Purchase type':  lambda a, u:  a.purchase_type_lookup,
    'Current':        lambda a, u:  wb( a._is_active ),
    'Last use':       lambda a, u:  tz( a.hist_modified ).date(),
    'Period end':     lambda a, u:  a.period_end_date,
    'Account':        lambda a, u:  a.account.name if a.account.is_group else
                                      u"Individual",
    'Is group':       lambda a, u:  wb( a.account.is_group ),
    'Pricing option': lambda a, u:  a.pa.name,
    'Subscription':   lambda a, u:  wb( a.is_subscription ),
    'Current price':  lambda a, u:  a.access_price,
    'Units':          lambda a, u:  a.sku_units,
    'Renewals':       lambda a, u:  a.renewals,
    'License tag':    lambda a, u:  a.tag_matches,
    'Trial':          lambda a, u:  wb( a.is_trial ),
    'Period start':   lambda a, u:  a.period_start_date,
    'Expires':        lambda a, u:  a.expire_date,
    'Description':    lambda a, u:  a.pa._description,
    'Coupon':         lambda a, u:  a.coupon,
    'Activated':      lambda a, u:  wb( a.is_activated ),
    'Create date':    lambda a, u:  tz( a.hist_created ).date(),
    'Create time':    lambda a, u:  tz( a.hist_created ).time(),
    'Last use time':  lambda a, u:  tz( a.hist_modified ).time(),
    }
if settings.DEBUG:
    pu_report['APA id'] = lambda a, u: a.pk
    pu_report['User id'] = lambda a, u: u.pk


@staff_required
def users_licenses_csv( request, start=None ):
    """
    This report combines licenses and users, so there is one row for
    every user/license combination
    It is organized by APAs, with expansion of all user/group relationships
    """
    def handler( _get ):
        log.info("START USER PURCHASE REPORT %s: %s -> %s", request.mptiming,
                                                         request.mpname, start)
        name = "UserLicenses"
        data = {
            'name': name,
            'start': start,
             }

        header = list( u1_report ) + list( pu_report ) + list( u2_report )

        job = SandboxReportJob( name, request, header, _user_licenses_rows_fn,
                                data=data )

        log.debug("Creating user blocks for license report: %s", job)
        blocks = define_user_blocks( job.sandbox_id,
                    settings.MP_REPORT['USER_BLOCK_SIZE'], start )
        for user_ids in blocks:
            job.add_report_task( user_ids=user_ids )

        job.start()

        return { 'report': name, 'start': start, 'blocks': len(blocks) }
    return respond_api_call( request, handler, methods=['GET'] )


def _user_row( user, data, writer ):

    for apa in user.apas.values():
        try:

            row_items = [ fn( user ) for fn in u1_report.values() ]
            row_items += [ fn( apa, user ) for fn in pu_report.values() ]
            row_items += [ fn( user ) for fn in u2_report.values() ]
            writer.writerow( row_items )

        except Exception as e:
            log.info2("Report user license exception: %s -> %s", user, e)
            if settings.MP_TESTING: raise

_user_rows_fn = user_rows_factory( _user_row )

@mp_async
def _user_licenses_rows_fn( **kwargs ):
    return _user_rows_fn( **kwargs )
