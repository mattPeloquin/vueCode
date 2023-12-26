#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Report job task
"""
from django.conf import settings

from mpframework.common import log
from mpframework.common.tasks import mp_async
from mpframework.common.tasks import Job
from mpframework.common.tasks import get_module_name
from mpframework.common.tasks.output import get_task_output
from mpframework.common.tasks.output import process_job_output_if_done
from mpframework.common.tasks.output import JOB_INCOMPLETE
from mpframework.common.tasks.spooler import ASYNC_RETRY
from mpframework.common.utils import timedelta_future
from mpframework.common.utils.time_utils import timestamp
from mpframework.common.email import send_email_user

from mpframework.foundation.tenant.models.sandbox import Sandbox
from mpframework.user.mpuser.models import mpUser

from . import report_writer


# Put a cap on report time as a sanity check; make configurable if needed
MAX_MINUTES = 60


@mp_async
def _complete_report( **kwargs ):
    """
    If the entire report job is complete, the Job process that completed the
    report aggregation will have a local copy of the report on its disk.
    Move this to S3 and then notify user it is ready.
    """
    job = kwargs['my_task']

    filename = process_job_output_if_done( **kwargs )
    if filename == JOB_INCOMPLETE:
        return ASYNC_RETRY

    sandbox = Sandbox.objects.get( id=job.sandbox_id )
    location = report_writer.push_report_to_s3( sandbox, filename )

    # TBD - make report email pretty

    user = job.report['user']
    user = mpUser.objects.get_user_from_email( user, sandbox )
    url = "https://{}/{}".format( settings.MP_ROOT_URLS['URL_PUBLIC'], location )

    info = ""
    if job.expired:
        info = "There was a problem running your report, it may not be complete"

    send_email_user( user, "Report is ready",
            "\nYour report is ready:\n{}\n{}".format( url, info )  )

    log.info("<= COMPLETED REPORT: %s -> %s", job.report['sandbox'], filename)


class SandboxReportJob( Job ):
    """
    Specialize MPF job for shared sandbox report functionality.

    FUTURE - take into account the Sandbox and User privledges of the
    site/person running the report and use to modify output
    """

    def __init__( self, name, request, header, rows_fn,
                  done_fn=_complete_report, **kwargs ):
        """
        Sandbox reports add information about the report context, and
        structure job/task execution as a set of blocks created by
        a setup_fn which are then executed by rows_fn in each sub task.
        """
        sandbox = request.sandbox
        self.sandbox_id = sandbox.pk

        # Store information specific about the report creation
        self.report = {
            'name': name,
            'sandbox': sandbox.subdomain,
            'user': request.user.email,
            'mpname': request.mpname,
            'header': header,
            'fn_name': get_module_name( rows_fn ),
            }

        # Support simple automated test verification on report output
        if settings.MP_TESTING_UNIT:
            self.report.update({ 'success_text': request.mptest['success_text'] })

        # Put reports in their own message group for each sandbox
        group = '{}_REPORT'.format( sandbox.unique_key )

        super().__init__( group, expires=timedelta_future( minutes=MAX_MINUTES ),
                    done_fn=done_fn, **kwargs )

    def __str__( self ):
        return str( self.report )

    def add_report_task( self, **kwargs ):
        """
        Create task based on the convention of using the report fn_name
        and passing the sandbox_id
        """
        return self.add_task( self.report['fn_name'],
                    sandbox_id=self.sandbox_id, **kwargs )

    def process_output( self ):
        """
        Override base output to get output from task sessions
        and write to local csv file whose filename is returned.
        ASSUMES JOB IS COMPLETE
        Returns the name of the local aggregated file.
        """
        log.info("Report job output: %s", self)

        # Create unique filename
        filename = '{}_{}_{}_{}.csv'.format( self.report['sandbox'],
                    self.report['user'], self.report['name'],
                    timestamp( fmt='%Y-%m%d-%H%M%S' ) )

        # Create local csv file
        with report_writer.get_report_file( filename ) as file:
            writer = report_writer.report_writer_file( file )
            writer.writerow( self.report['header'] )

            # Write the session chunks
            for task_session in self.task_keys:
                output = get_task_output( self.cache, task_session )
                if output:
                    file.write( output )

                    # Automated test check - ASSUMES ONE BLOCK/TASK!!!
                    if settings.MP_TESTING:
                        text = self.report['success_text']
                        if text not in output:
                            raise Exception("BAD REPORT SUCCESS TEXT: %s -> %s\n%s" %
                                             (self, text, output))
        self.cleanup()
        return filename
