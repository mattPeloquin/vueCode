#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Public file admin
"""

from mpframework.common.form import BaseModelForm
from mpframework.common.admin import root_admin
from mpframework.common.admin import staff_admin
from mpframework.common.admin import StaffAdminMixin
from mpframework.foundation.tenant.admin import BaseTenantAdmin

from ..models import PublicFile


class PublicFileForm( BaseModelForm ):
    class Meta:
        model = PublicFile
        exclude = ()

        labels = dict( BaseModelForm.Meta.labels, **{
            '_name': "UI Name",
            'filename': "File to upload",
            })
        help_texts = dict( BaseModelForm.Meta.help_texts, **{
            '_name': "Optional staff UI name for this file.<br>"
                "Defaults to the filename",
            'filename': "Once file is uploaded it can be accessed through the "
                "EasyLink. If a new file is uploaded it will replace all "
                "existing uses of the file.",
            })
        widgets = dict( BaseModelForm.Meta.widgets, **{
            })


class PublicFileAdmin( BaseTenantAdmin ):
    form = PublicFileForm

    list_display = ( 'name', 'sandbox', 'easylink' )
    ordering = ( 'filename' ,)

    list_filter = ( 'sandbox' ,)
    search_fields = ( '_name', 'filename' )

    fieldsets = [
        ('', {
            'classes': ('mp_collapse',),
            'fields': (
                '_name',
                'filename',
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

    def save_model( self, request, obj, form, change ):
        if not obj.name:
            obj.name = obj.filename.name
        super().save_model( request, obj, form, change )

    def name( self, obj ):
        return obj.name
    name.short_description = "Name"
    name.admin_order_field = '_name'

    def easylink( self, obj ):
        return obj.filename.url
    easylink.short_description = "EasyLink"
    easylink.admin_order_field = 'filename'

root_admin.register( PublicFile, PublicFileAdmin )


class PublicFileStaffAdmin( StaffAdminMixin, PublicFileAdmin ):
    pass

staff_admin.register( PublicFile, PublicFileStaffAdmin )
