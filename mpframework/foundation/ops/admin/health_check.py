#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Staff screens for view history changes
"""
from mpframework.common.admin import BaseModelAdmin
from mpframework.common.admin import root_admin

from ..models import HealthCheck


class HealthCheckRootAdmin( BaseModelAdmin ):
    no_tenant_filter = True
    list_display = ( 'server', 'checks' )
    list_filter = ( 'server', 'hist_modified' )

root_admin.register( HealthCheck, HealthCheckRootAdmin )
