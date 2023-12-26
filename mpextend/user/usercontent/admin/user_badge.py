#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    User badge admin
"""
from django import forms

from mpframework.common import constants as mc
from mpframework.common.form import BaseModelForm
from mpframework.common.admin import root_admin
from mpframework.common.admin import staff_admin
from mpframework.common.admin import StaffAdminMixin
from mpframework.common.admin.large import AdminLargeMixin
from mpframework.foundation.tenant.admin import BaseTenantAdmin

from ..models import UserBadge


class UserBadgeForm( BaseModelForm ):
    autolookup_fields = ('cu', 'badge')
    class Meta:
        model = UserBadge
        exclude = ()

        labels = dict( BaseModelForm.Meta.labels, **{
            'progress_data': "Progress data",
            'hist_created': "Started",
            })
        help_texts = dict( BaseModelForm.Meta.help_texts, **{
            'progress_data': "Data related to the badge accomplishment.",
            })
        widgets = dict( BaseModelForm.Meta.widgets, **{
            'progress_data': forms.Textarea( attrs=mc.UI_TEXTAREA_LARGE ),
            })

class BaseUserBadgeAdmin( BaseTenantAdmin ):
    form = UserBadgeForm

    list_display = ( 'cu', 'badge', 'progress', 'completed' )
    list_display_links = ( 'cu' ,)
    list_editable = ( 'progress' ,)
    search_fields = ( 'cu__user__email', 'cu__user__first_name', 'cu__user__last_name',
                      'badge__badge_tag', 'badge___name' )
    list_filter = ( 'progress', 'hist_modified', 'hist_created' )

    readonly_fields = BaseTenantAdmin.readonly_fields + ( 'cu', 'badge' )

    fieldsets = [
        ('', {
            'fields': (
                ('cu', 'badge'),
                ('progress', 'completed'),
                ('hist_modified', 'hist_created'),
                ),
            }),
        ("Admin", {
            'mp_staff_level': 'access_high',
            'classes': ('mp_collapse mp_closed',),
            'fields': (
                'progress_data',
                ),
            }),
        ('ROOT', {
            'mp_staff_level': 'access_root_menu',
            'classes': ('mp_collapse mp_closed',),
            'fields': (
                )
            }),
        ]


class UserBadgeStaffAdmin( StaffAdminMixin, AdminLargeMixin, BaseUserBadgeAdmin ):
    can_add_item = False

staff_admin.register( UserBadge, UserBadgeStaffAdmin )


class UserBadgeRootAdmin( AdminLargeMixin, BaseUserBadgeAdmin ):
    pass

root_admin.register( UserBadge, UserBadgeRootAdmin )
