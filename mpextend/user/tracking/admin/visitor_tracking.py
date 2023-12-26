#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Admin for Visitor Tracking
"""
from django import forms

from mpframework.common import constants as mc
from mpframework.common.form import BaseModelForm
from mpframework.common.admin import root_admin
from mpframework.common.admin import BaseAdmin

from ..models import VisitorTracking


class VisitorTrackingForm( BaseModelForm ):
    """
    This form is used for editing user tracking values in provider and root admin
    """
    class Meta:
        model = VisitorTracking
        exclude = ()

        labels = dict( BaseModelForm.Meta.labels, **{
            })
        widgets = dict( BaseModelForm.Meta.widgets, **{
            'sessions': forms.Textarea( attrs={'rows': '16', 'cols': mc.CHAR_LEN_UI_LINE} ),
            })


class VisitorTrackingAdmin( BaseAdmin ):
    no_tenant_filter = True
    form = VisitorTrackingForm

    list_display = ( 'ip_address', 'sandbox', 'requests', 'location',
                'device', 'last_update' )
    list_filter = ( 'sandbox', 'hist_created', 'last_update' )
    search_fields = ( 'ip_address' ,)

    ordering = ( '-last_update' ,)

    can_add_item = False

    def location( self, obj ):
        return obj.geoip.location
    location.short_description = "Location"

    def device( self, obj ):
        return obj.device
    device.short_description = "Device"

root_admin.register( VisitorTracking, VisitorTrackingAdmin )
