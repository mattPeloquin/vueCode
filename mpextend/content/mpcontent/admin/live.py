#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Live event admin

    There are a lot of permutations for how events can be configured
    so the admin add/edit page is driven significantly by hiding/showing
    different fields depending on the event type shown.
"""
from django import forms

from mpframework.common import constants as mc
from mpframework.common.admin import root_admin
from mpframework.common.admin import staff_admin
from mpframework.common.admin import StaffAdminMixin
from mpframework.common.form import mpFileFieldFormMixin
from mpframework.common.widgets import HtmlEditor
from mpframework.common.widgets import CodeEditor
from mpframework.content.mpcontent.admin import BaseItemAdmin
from mpframework.content.mpcontent.admin import BaseItemForm

from ..models import LiveEvent


class LiveEventForm( mpFileFieldFormMixin, BaseItemForm ):
    class Meta:
        model = LiveEvent
        exclude = ()

        labels = dict( BaseItemForm.Meta.labels, **{
            'event_type': "Event type",
            'proxy_main': "URL for event",
            'invite_html': "Event invite",
            'event_id': "Event ID",
            'event_account': "Account ID",
            'event_password': "Event password",
            '_available': "Start date and time",
            'minutes_length': "Length of event in minutes",
            'minutes_open': "Minutes before start to open event",
            'minutes_close': "Minutes after start to close event",
            '_proxy_options': "Advanced options",
            })
        labels_sb = dict( BaseItemForm.Meta.labels_sb, **{
            })
        help_texts = dict( BaseItemForm.Meta.help_texts, **{
            'event_type': "Select the type of event",
            'proxy_main': "Paste the event's link here",
            'invite_html': "Paste text or HTML for the event invite here",
            'event_id': "The ID, name, or code for the event",
            'event_password': "Optionally a password users must enter",
            'event_account': "If required by your platform, enter the platform account ID",
            '_available': "Enter the date and time the event will start.<br>"
                    "Before the event is open a timer is shown.<br>"
                    "Leave blank for a perpetual event.",
            'minutes_length': "Length of event in minutes. Used for calendar invites "
                    "and as a default length to allow users to connect to the event.",
            'minutes_open': "Optional number of minutes before the event's start "
                    "to allow users to connect to the event.",
            'minutes_close': "Optional override of event length, enter the minutes "
                    "after start time to close event.",
            '_proxy_options': "Add options to fixup request or response.<br>"
                    "{help_proxy_options}",
            })
        widgets = dict( BaseItemForm.Meta.widgets, **{
            'proxy_main': forms.TextInput( attrs=mc.UI_TEXT_SIZE_XLARGE ),
            'event_id': forms.TextInput( attrs=mc.UI_TEXT_SIZE_XLARGE ),
            'event_account': forms.TextInput( attrs=mc.UI_TEXT_SIZE_DEFAULT ),
            'event_password': forms.TextInput( attrs=mc.UI_TEXT_SIZE_DEFAULT ),
            'invite_html': HtmlEditor( rows=16 ),
            '_proxy_options': CodeEditor( mode='yaml', rows=8 ),
            })


class LiveEventAdmin( BaseItemAdmin ):
    form = LiveEventForm

    list_display = BaseItemAdmin.LIST_START + (
            'available' ,) + BaseItemAdmin.LIST_END
    list_text_small = BaseItemAdmin.list_text_small + (
            'available' ,)

    list_filter = BaseItemAdmin.list_filter + ( '_available' ,)

    def __init__( self, *args, **kwargs ):
        super().__init__( *args, **kwargs )
        self.ld_insert_pos = 4

    def get_fieldsets( self, request, obj=None ):
        rv = super().get_fieldsets( request, obj )
        user = request.user

        # Add event-specific fields
        new_rows = [
            ('event_type', '_available'),
            ('minutes_length',),
            ('minutes_open','minutes_close'),
            ('invite_html',),
            ('proxy_main',),
            ('event_id',),
            ('event_account', 'event_password'),
            ]
        if user.access_high:
            # Remove original available datetime so it won't override in POST
            rv[ self.fs_options ][1]['fields'][3] = ('internal_tags',)
        if user.access_all:
            new_rows.append( ('_proxy_options',) )
        rv[ self.fs_content ][1]['fields'][0:0] = new_rows

        return rv

    def available( self, obj ):
        return obj.available
    available.short_description = "Available"
    available.admin_order_field = '_available'

root_admin.register( LiveEvent, LiveEventAdmin )


class LiveEventStaffAdmin( StaffAdminMixin, LiveEventAdmin ):
    pass

staff_admin.register( LiveEvent, LiveEventStaffAdmin )
