#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    ProtectedFile admin
"""

from mpframework.common.admin import root_admin
from mpframework.common.admin import staff_admin
from mpframework.common.admin import StaffAdminMixin
from mpframework.common.form import mpFileFieldFormMixin

from . import BaseItemAdmin
from . import BaseItemForm
from ..models import ProtectedFile


class ProtectedFileForm( mpFileFieldFormMixin, BaseItemForm ):
    class Meta:
        model = ProtectedFile
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

    def __init__( self, *args, **kwargs ):
        super().__init__( *args, **kwargs )

        # Add additional action types
        if self.fields.get('_action'):
            self.fields['_action'].choices += ProtectedFile.ACTION_ATTACHMENT


class ProtectedFileAdminBase( BaseItemAdmin ):
    form = ProtectedFileForm

    list_display = BaseItemAdmin.LIST_START + (
            'display_name', 'display_mb',
            ) + BaseItemAdmin.LIST_END

    search_fields = BaseItemAdmin.search_fields + ( 'content_file', )

    def get_fieldsets( self, request, obj=None ):
        rv = super().get_fieldsets( request, obj )
        user = request.user

        rv[ self.fs_content ][1]['fields'].insert( 0, ('content_file','_action') )

        if user.access_root:
            rv[ self.fs_content ][1]['fields'].insert( 1, ('content_file_bytes',))
        return rv

    def display_name( self, obj ):
        return obj.content_file_name
    display_name.short_description = "File Name"

    def display_mb( self, obj ):
        return obj.content_file_mb
    display_mb.short_description = "File Size"


class ProtectedFileRootAdmin( ProtectedFileAdminBase ):
    list_display = ProtectedFileAdminBase.list_display + ( '_content_file', )
    def _content_file( self, obj ):
        return obj.content_file.name

root_admin.register( ProtectedFile, ProtectedFileRootAdmin )


class ProtectedFileStaffAdmin( StaffAdminMixin, ProtectedFileAdminBase ):
    pass

staff_admin.register( ProtectedFile, ProtectedFileStaffAdmin )
