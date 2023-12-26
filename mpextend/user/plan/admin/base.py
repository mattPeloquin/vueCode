#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared admin functionality for plans
"""

from mpframework.common.admin import root_admin
from mpframework.foundation.tenant.admin import BaseTenantAdmin

from ..models import BasePlan


class BasePlanAdmin( BaseTenantAdmin ):

    list_display = ( 'top_count', 'content', 'hist_created', 'hist_modified' )


    def top_count( self, inst ):
        top_ids = inst.top_ids
        return len( top_ids ) if isinstance( top_ids, list ) else 0
    top_count.short_description = "Plan collections"
    top_count.admin_order_field = 'content'


root_admin.register( BasePlan, BasePlanAdmin )

