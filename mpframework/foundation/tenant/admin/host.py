#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Sandbox host admin
"""

from mpframework.common.admin import root_admin

from ..models.sandbox_host import SandboxHost
from . import BaseTenantAdmin


class SandboxHostAdmin( BaseTenantAdmin ):
    no_tenant_filter = True

    ordering = ( 'sandbox___provider__name', 'sandbox_id', '_host_name' )

    list_display = ( '_provider', 'sandbox', '_host_name', 'main',
                        'https', 'redirect_to_main' )
    list_display_links = ( 'sandbox' ,)
    list_editable = ( '_host_name', 'main', 'https' )
    list_filter = ( 'sandbox___provider' ,)

    search_fields = ( 'sandbox__name', 'sandbox___provider__name', '_host_name' )

    def _provider( self, obj ):
        return obj.sandbox.provider
    _provider.short_description = "Provider"
    _provider.admin_order_field = 'sandbox___provider'

root_admin.register( SandboxHost, SandboxHostAdmin )
