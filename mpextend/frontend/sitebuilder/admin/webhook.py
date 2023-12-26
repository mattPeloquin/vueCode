#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Public file admin
"""
from django import forms

from mpframework.common import constants as mc
from mpframework.common.form import BaseModelForm
from mpframework.common.admin import root_admin
from mpframework.common.admin import staff_admin
from mpframework.common.admin import StaffAdminMixin
from mpframework.foundation.tenant.admin import BaseTenantAdmin

from ..models import WebHook


class WebHookForm( BaseModelForm ):
    class Meta:
        model = WebHook
        exclude = ()

        labels = dict( BaseModelForm.Meta.labels, **{
            'name': "Webhook name",
            'url': "URL to call",
            'hook_event': "Type of event",
            'hook_data': "How to send data",
            })
        help_texts = dict( BaseModelForm.Meta.help_texts, **{
            'name': "Internal name for your webhook",
            'url': "The URL to call when an event occurs",
            'hook_event': "The system event to call the URL for",
            'hook_data': "How should the data be sent to the url",
            })
        widgets = dict( BaseModelForm.Meta.widgets, **{
            })


class WebHookAdmin( BaseTenantAdmin ):
    form = WebHookForm

    list_display = ( 'name', 'hook_event', 'url', 'hook_data' )
    ordering = ( 'name' ,)

    list_filter = ( 'hook_event', 'hook_data' )
    search_fields = ( 'name', 'url' )

    fieldsets = [
        ('', {
            'classes': ('mp_collapse',),
            'fields': (
                'name',
                ('hook_event', 'hook_data'),
                'url',
                'notes',
                )
            }),
        ('ROOT', {
            'mp_staff_level': 'access_root_menu',
            'classes': ('mp_collapse mp_closed',),
            'fields': (
                'sandbox',
                ('hist_created', 'hist_modified'),
                )
            }),
        ]

root_admin.register( WebHook, WebHookAdmin )


class WebHookStaffAdmin( StaffAdminMixin, WebHookAdmin ):
    pass

staff_admin.register( WebHook, WebHookStaffAdmin )
