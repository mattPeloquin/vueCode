#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared code for admin user reports
"""
from django.conf import settings
from django.db.utils import OperationalError

from mpframework.common import log
from mpframework.common.logging.timing import mpTiming
from mpframework.common.tasks import spool_breathe

from ..report_writer import report_writer_string
from .._utils.user_block import get_user_block_info


def user_rows_factory( user_row_fn ):
    """
    Factory code for creating per-user report output
    """
    def user_rows_fn( **kwargs ):
        task = kwargs['my_task']

        if not task.job:
            msg = "USER REPORT JOB EXPIRED: %s" % str(task)
            if settings.MP_TESTING:
                raise Exception( msg )
            else:
                log.warning_quiet( msg )
                return ''

        log.debug("Starting task block: %s", task)
        t = mpTiming()

        sandbox_id = kwargs['sandbox_id']
        user_ids = kwargs['user_ids']
        data = task.job.data
        name = data['name']

        user_info = get_user_block_info( sandbox_id, user_ids, t, data.get('detailed') )
        users = user_info['users']

        writer = report_writer_string()

        errors = False
        user_num = 1
        for user in users.values():
            spool_breathe( user_num )
            try:
                log.detail3("Creating %s row: %s -> %s", name, user_num, user)

                user_row_fn( user, data, writer )

            except OperationalError:
                # Most likely DB connection needs reset, let caller manage
                raise
            except Exception as e:
                # Try to carry on in the face of data or code proplem
                log.info2("Report %s exception: %s -> %s", name, user, e)
                if settings.MP_TESTING:
                    raise
                log.debug_on() and log.exception_quiet("")
                errors = True

            user_num += 1
        errors and log.warning_quiet("Report errors %s: %s", name, task.job.report['mpname'])
        log.info2("<= %s %s block: %s users -> %s", t, name, len(users), task)

        return writer.output.getvalue()

    return user_rows_fn
