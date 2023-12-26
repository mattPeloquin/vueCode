#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Admin screens for group plans
"""

from mpframework.common.admin import root_admin

from ..models import GroupPlan
from .base import BasePlanAdmin


class GroupPlanAdmin( BasePlanAdmin ):

    list_display = ( '_name', 'group_account' ) + BasePlanAdmin.list_display

    list_filter = ( 'group_account' ,) + BasePlanAdmin.list_filter
    search_fields = ( '_name', 'group_account__base_account__name' )

root_admin.register( GroupPlan, GroupPlanAdmin )

