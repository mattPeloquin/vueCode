#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Report of all system sandboxes
"""
from django.http import HttpResponseRedirect

from mpframework.common import log
from mpframework.common.tasks import mp_async
from mpframework.common.utils import tz
from mpframework.common.view import root_only
from mpframework.foundation.tenant.models import Sandbox
from mpextend.foundation.reports.jobs import SandboxReportJob
from mpextend.foundation.reports.report_writer import report_writer_string


_report = {
    "Subdomain":        lambda s:  s.subdomain,
    "Name":             lambda s:  s.name,
    "Staff email":      lambda s:  s.email_staff,
    "URL":              lambda s:  s.portal_url(),
    "Created":          lambda s:  tz( s.hist_created ).date(),
    "Modified":         lambda s:  tz( s.hist_modified ).date(),
    "Provider":         lambda s:  s._provider.name,
    "Support email":    lambda s:  s.email_support,
    "TimeZone":         lambda s:  s.timezone,
    "Theme":            lambda s:  s.theme and s.theme.name,
    "Summary":          lambda s:  s.summary,
    "NotifyLevel":      lambda s:  s.notify_level,
    "Policy":           lambda s:  s.policy,
    "ResourcePath":     lambda s:  s.resource_path,
    "Options":          lambda s:  s.options,
    "ID":               lambda s:  s.pk,
    }

@root_only
def sites_csv( request ):
    log.info("ROOT SITE REPORT: %s", request.mpname)

    name = "sites_summary"
    data = {
        'name': name,
        }
    header = list( _report )

    job = SandboxReportJob( name, request, header, _rows_fn, data=data )
    sandbox_ids = Sandbox.objects.mpusing('read_replica').order_by('id')\
                .values_list( 'id', flat=True )

    job.add_report_task( sandbox_ids=sandbox_ids )
    job.start()

    return HttpResponseRedirect( request.referrer )

@mp_async
def _rows_fn( **kwargs ):
    writer = report_writer_string()
    for sandbox_id in kwargs['sandbox_ids']:

        sandbox = Sandbox.objects.mpusing('read_replica')\
                    .select_related( '_provider', 'theme' )\
                    .get( id=sandbox_id )

        row_items = [ fn( sandbox ) for fn in _report.values() ]

        writer.writerow( row_items )

    return writer.output.getvalue()
