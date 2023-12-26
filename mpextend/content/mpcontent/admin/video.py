#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Video admin
"""

from mpframework.common.admin import root_admin
from mpframework.common.admin import staff_admin
from mpframework.common.admin import StaffAdminMixin
from mpframework.common.form import mpFileFieldFormMixin
from mpframework.content.mpcontent.admin import BaseItemAdmin
from mpframework.content.mpcontent.admin import BaseItemForm

from ..models import Video


class VideoForm( mpFileFieldFormMixin, BaseItemForm ):
    class Meta:
        model = Video
        exclude = ()

        labels = dict( BaseItemForm.Meta.labels, **{
            'file_med': "Default video file",
            'file_high': "High bandwidth file",
            'file_low': "Low bandwidth file",
            '_poster': "Poster image",
            })
        labels_sb = dict( BaseItemForm.Meta.labels_sb, **{
            })
        help_texts = dict( BaseItemForm.Meta.help_texts, **{
            'file_med': "Upload the video file users will view",
            'file_high': "Optionally provide a higher definition file users can select "
                    "for faster networks and larger screens",
            'file_low': "Optional provide a lower resolution file users can select "
                    "for slower links (e.g., some mobile)",
            '_poster': "Optional image displayed before playback; defaults "
                    "to main image if provided or first frame of video.",
            })
        widgets = dict( BaseItemForm.Meta.widgets, **{
            })


class VideoBaseAdmin( BaseItemAdmin ):
    form = VideoForm

    list_display = BaseItemAdmin.LIST_START + (
            'display_name', 'display_mb',
            ) + BaseItemAdmin.LIST_END
    list_text_small = BaseItemAdmin.list_text_small + (
            'display_name', 'display_mb' )

    def get_fieldsets( self, request, obj=None ):
        rv = super().get_fieldsets( request, obj )
        user = request.user

        new_rows = [
            ('file_med',),
            ]
        if user.access_high:
            new_rows += [
                '_poster',
                'html3',
                ]
        if user.access_all:
            new_rows.insert( 2, ('file_low','file_high') )
        rv[ self.fs_content ][1]['fields'][0:0] = new_rows

        if user.access_root:
            rv[-1][1]['fields'].extend([
                ('file_low_bytes',),
                ('file_med_bytes',),
                ('file_high_bytes'),
                ])
        return rv

    def display_name( self, obj ):
        return obj.file_med_name
    display_name.short_description = "File Name"

    def display_mb( self, obj ):
        return obj.file_med_mb
    display_mb.short_description = "File Size"


class VideoRootAdmin( VideoBaseAdmin ):
    list_display = VideoBaseAdmin.LIST_START + (
            'file_med' ,) + VideoBaseAdmin.LIST_END

root_admin.register( Video, VideoRootAdmin )


class VideoStaffAdmin( StaffAdminMixin, VideoBaseAdmin ):
    pass

staff_admin.register( Video, VideoStaffAdmin )
