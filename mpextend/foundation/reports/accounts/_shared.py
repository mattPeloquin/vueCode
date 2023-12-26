#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    All of the GA reports are based on users in the group
    account, much of the code is shared here
"""
from django.conf import settings

from mpframework.common import log
from mpframework.common.utils.http import clean_url

from ..jobs import SandboxReportJob
from .._utils.user_block import get_account_user_blocks


def start_ga_report( request, account, header, rows_fn, data=None, detailed=False ):
    """
    Shared code in GA report handlers to start job
    """
    if not account:
        return
    log.info("GA REPORT Users: %s -> %s", request.mpname, account)

    name = u"{}_summary".format( clean_url( account.name ) )
    data = data or {}
    data.update({
        'name': name,
        'detailed': detailed,
        })

    job = SandboxReportJob( name, request, header, rows_fn, data=data )

    log.debug("Creating user blocks for GA report: %s -> %s", account, job)
    blocks = get_account_user_blocks( account, settings.MP_REPORT['USER_BLOCK_SIZE'] )
    for user_ids in blocks:
        job.add_report_task( user_ids=user_ids )

    job.start()

    return { 'report': name, 'detailed': detailed, 'blocks': len(blocks) }
