#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Single report with maximum user info
"""
from decimal import Decimal
from django.conf import settings

from mpframework.common import log
from mpframework.common.tasks import mp_async
from mpframework.common.utils import tz
from mpframework.common.utils.strings import wb
from mpframework.common.view import staff_required
from mpframework.common.api import respond_api_call
from mpextend.product.account.models import GroupAccount

from ..jobs import SandboxReportJob
from .._utils import email_host
from .._utils import email_group
from .._utils.user_block import define_user_blocks
from .._utils.user_content_summary import content_headers
from .._utils.user_content_summary import content_row_items
from .._utils.user_rows import user_rows_factory


u1_report = {
    'Email':      lambda u:  u.email,
    'First name': lambda u:  u.first_name,
    'Last name':  lambda u:  u.last_name,
    'Account':    lambda u:  "" if not u.account else
            u.account.name if u.account.is_group else u"Individual",
    }
apa_report = {
    'Active licenses': lambda apas:
            len([ a for a in apas if a._is_active ]) if apas else '',
    'Free licenses':   lambda apas:
            len([ a for a in apas if a.access_free ]) if apas else '',
    'Paid licenses':   lambda apas:
            len([ a for a in apas if not a.access_free ]) if apas else '',
    'Coupons':         lambda apas:
            len([ a for a in apas if a.coupon ]) if apas else '',
    'Total paid':      lambda apas:
            sum([ Decimal(a.data.get('total_paid', 0)) for a in apas ])
                    if apas else '',
    }
u2_report = {
    'Last active':     lambda u:  tz( u.tracking.last_update ).date(),
    'Join date':       lambda u:  tz( u.hist_created ).date(),
    'Organization':    lambda u:  u.organization,
    'Title':           lambda u:  u.title,
    'Email group':     lambda u:  email_group( u.email ),
    'Items used':      lambda u:  len( u.useritems ),
    'Collections':     lambda u:  len( u.usertops ),
    'User minutes':    lambda u:  u.total_mins,
    'Last country':    lambda u:  u.geo.country,
    'Last region':     lambda u:  u.geo.region,
    'Last city':       lambda u:  u.geo.city,
    'Last postal':     lambda u:  u.geo.postal,
    'User tag1':       lambda u:  u.external_tag,
    'User tag2':       lambda u:  u.external_tag2,
    'User tag3':       lambda u:  u.external_tag3,
    }
u3_report = {
    'External ID':     lambda u:  u.external_key,
    'Custom groups':   lambda u:  u.external_group,
    'Disabled':        lambda u:  wb( not u.is_active ),
    'Activated':       lambda u:  wb( u.activated ),
    'Terms accepted':  lambda u:  wb( u.terms_accepted ),
    'Email verified':  lambda u:  wb( u.email_verified ),
    'Email host':      lambda u:  email_host( u.email ),
    'Logins':          lambda u:  u.tracking.logins,
    'Other minutes':   lambda u:  u.tracking.minutes,
    'Workflow':        lambda u:  wb( u.get_workflow_level_display() ),
    'Avatar image':    lambda u:  wb( u.image ),
    'Last use time':   lambda u:  tz( u.tracking.last_update ).time(),
    'Join time':       lambda u:  tz( u.hist_created ).time(),
    'Last latitude':   lambda u:  u.geo.latitude,
    'Last longitude':  lambda u:  u.geo.longitude,
    }
if settings.DEBUG:
    u3_report['id'] = lambda u: u.pk

@staff_required
def users_summary_csv( request, start=None ):
    """
    Single report with maximum user info
    """
    def handler( _get ):
        log.info("START USER SUMMARY REPORT %s: %s -> %s",
                    request.mptiming, request.mpname, start)
        name = "UserSummary"

        # Share data with every task through cache
        gas = GroupAccount.objects\
                    .mpusing('read_replica')\
                    .filter( sandbox=request.sandbox )
        data = {
            'name': name,
            'start': start,
            'gas': { ga.id: ga for ga in gas.iterator() },
            }
        log.debug("User summary report data: %s", data)

        header = list( u1_report ) + content_headers( items=False ) + list(
                    apa_report ) + list( u2_report ) + list( u3_report )

        job = SandboxReportJob( name, request, header, _users_summary_rows_fn, data=data )

        log.debug("Creating user blocks for summary report: %s", job)
        blocks = define_user_blocks( job.sandbox_id,
                    settings.MP_REPORT['USER_BLOCK_SIZE'], start )
        for user_ids in blocks:
            job.add_report_task( user_ids=user_ids )

        job.start()

        return { 'report': name, 'start': start, 'blocks': len(blocks) }
    return respond_api_call( request, handler, methods=['GET'] )

def _user_row( user, data, writer ):

    row_items = [ fn( user ) for fn in u1_report.values() ]
    row_items += content_row_items( user, items=False )
    row_items += [ fn( user.apas.values() ) for fn in apa_report.values() ]
    row_items += [ fn( user ) for fn in u2_report.values() ]
    row_items += [ fn( user ) for fn in u3_report.values() ]

    writer.writerow( row_items )

_user_rows_fn = user_rows_factory( _user_row )

@mp_async
def _users_summary_rows_fn( **kwargs ):
    return _user_rows_fn( **kwargs )
