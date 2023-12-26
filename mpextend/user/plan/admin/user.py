#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Admin screens for user plans
"""
from django import forms

from mpframework.common import constants as mc
from mpframework.common.admin import root_admin
from mpframework.common.admin import staff_admin
from mpframework.common.admin import StaffAdminMixin
from mpframework.common.form import BaseModelForm

from ..models import UserPlan
from .base import BasePlanAdmin


class UserPlanForm( BaseModelForm ):
    class Meta:
        model = UserPlan
        exclude = ()

        labels = dict( BaseModelForm.Meta.labels, **{
            })
        help_texts = dict( BaseModelForm.Meta.help_texts, **{
            })
        widgets = dict( BaseModelForm.Meta.widgets, **{
            'content': forms.Textarea( attrs={'rows': 16, 'cols': mc.CHAR_LEN_UI_LINE} ),
            })


class UserPlanAdmin( BasePlanAdmin ):
    form = UserPlanForm

    list_display = ( '_user' ,) + BasePlanAdmin.list_display

    search_fields = ( '_user__email' ,)

    readonly_fields = ( '_user' ,) + BasePlanAdmin.readonly_fields

    fieldsets = [
        ("", {
            'classes': ('mp_collapse',),
            'fields': (
                '_user',
                'content',
                )
            }),
        ('ROOT', {
            'classes': ('mp_collapse',),
            'mp_staff_level': 'access_root_menu',
            'fields': (
                ('hist_created', 'hist_modified'),
                )
            }),
        ]

root_admin.register( UserPlan, UserPlanAdmin )


class UserPlanStaffAdmin( StaffAdminMixin, UserPlanAdmin ):
    can_add_item = False

staff_admin.register( UserPlan, UserPlanStaffAdmin )

