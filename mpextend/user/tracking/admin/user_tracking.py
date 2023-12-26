#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Admin for mpUser Tracking
"""
from django import forms

from mpframework.common import constants as mc
from mpframework.common.form import BaseModelForm
from mpframework.common.admin import root_admin
from mpframework.common.admin import BaseAdmin

from ..models import UserTracking


class mpUserTrackingForm( BaseModelForm ):
    """
    This form is used for editing user tracking values in provider and root admin
    """
    class Meta:
        model = UserTracking
        exclude = ()

        labels = dict( BaseModelForm.Meta.labels, **{
            'ui_state': "Portal State",
            'info': "Tracking info",
            })
        widgets = dict( BaseModelForm.Meta.widgets, **{
            'ui_state': forms.Textarea( attrs={'rows': '8', 'cols': mc.CHAR_LEN_UI_LINE} ),
            'sessions': forms.Textarea( attrs={'rows': '16', 'cols': mc.CHAR_LEN_UI_LINE} ),
            'info': forms.Textarea( attrs={'rows': '24', 'cols': mc.CHAR_LEN_UI_LINE} ),
            })


class UserTrackingAdmin( BaseAdmin ):
    no_tenant_filter = True
    form = mpUserTrackingForm

    list_display = ( 'user', 'logins', 'minutes', 'ip_address', 'location',
                'device', 'last_update' )
    list_filter = ( 'user___sandbox', 'hist_created', 'last_update' )
    search_fields = ( 'user__email', 'user___sandbox__name', 'user___provider__name',
                      'ip_address' )

    ordering = ( '-last_update' ,)

    # Don't want to change this, and can't have UI creating list of all users
    readonly_fields = ( 'user' ,)

    can_add_item = False

    def minutes( self, obj ):
        return obj.minutes
    minutes.short_description = "Minutes"

    def location( self, obj ):
        return obj.geoip.location
    location.short_description = "Location"

    def device( self, obj ):
        return obj.device
    device.short_description = "Device"

root_admin.register( UserTracking, UserTrackingAdmin )

