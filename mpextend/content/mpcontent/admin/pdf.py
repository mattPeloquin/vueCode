#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    PDF content admin
"""

from mpframework.common.admin import root_admin
from mpframework.common.admin import staff_admin
from mpframework.common.admin import StaffAdminMixin
from mpframework.common.form import mpFileFieldFormMixin
from mpframework.content.mpcontent.admin import BaseItemAdmin
from mpframework.content.mpcontent.admin import BaseItemForm

from ..models import PDF


class PdfForm( mpFileFieldFormMixin, BaseItemForm ):
    class Meta:
        model = PDF
        exclude = ()

        labels = dict( BaseItemForm.Meta.labels, **{
            'content_file': "Content file",
            })
        labels_sb = dict( BaseItemForm.Meta.labels_sb, **{
            })
        help_texts = dict( BaseItemForm.Meta.help_texts, **{
            'content_file': "Upload the file that users will download",
            })
        widgets = dict( BaseItemForm.Meta.widgets, **{
            })


class PdfAdminBase( BaseItemAdmin ):
    form = PdfForm

    list_display = BaseItemAdmin.LIST_START + (
            'display_name', 'display_mb',
            ) + BaseItemAdmin.LIST_END

    search_fields = BaseItemAdmin.search_fields + ( 'content_file', )

    def get_fieldsets( self, request, obj=None ):
        rv = super().get_fieldsets( request, obj )
        user = request.user

        new_row = ( 'content_file' ,)
        rv[ self.fs_content ][1]['fields'].insert( 0, new_row )

        if user.access_root:
            rv[ self.fs_content ][1]['fields'].insert( 1, ('content_file_bytes',))
        return rv

    def display_name( self, obj ):
        return obj.content_file_name
    display_name.short_description = "File Name"

    def display_mb( self, obj ):
        return obj.content_file_mb
    display_mb.short_description = "File Size"


class PdfRootAdmin( PdfAdminBase ):
    list_display = PdfAdminBase.list_display + ( '_content_file', )
    def _content_file( self, obj ):
        return obj.content_file.name

root_admin.register( PDF, PdfRootAdmin )


class PdfStaffAdmin( StaffAdminMixin, PdfAdminBase ):
    pass

staff_admin.register( PDF, PdfStaffAdmin )
