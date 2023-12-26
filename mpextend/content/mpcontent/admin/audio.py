#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Audio content admin
"""

from mpframework.common.admin import root_admin
from mpframework.common.admin import staff_admin
from mpframework.common.admin import StaffAdminMixin
from mpframework.common.form import mpFileFieldFormMixin
from mpframework.content.mpcontent.admin import BaseItemAdmin
from mpframework.content.mpcontent.admin import BaseItemForm

from ..models import Audio


class AudioForm( mpFileFieldFormMixin, BaseItemForm ):
    class Meta:
        model = Audio
        exclude = ()

        labels = dict( BaseItemForm.Meta.labels, **{
            'audio_file': "Streaming audio file",
            '_poster': "Poster image",
            })
        labels_sb = dict( BaseItemForm.Meta.labels_sb, **{
            })
        help_texts = dict( BaseItemForm.Meta.help_texts, **{
            'audio_file': "Upload the audio file the user will listen to",
            '_poster': "Optional image displayed during playback; defaults "
                    "to main image if provided",
            })
        widgets = dict( BaseItemForm.Meta.widgets, **{
            })


class AudioBaseAdmin( BaseItemAdmin ):
    form = AudioForm

    list_display = BaseItemAdmin.LIST_START + (
        'display_name', 'display_mb',
        ) + BaseItemAdmin.LIST_END
    list_text_small = BaseItemAdmin.list_text_small + (
            'display_name', 'display_mb' )

    search_fields = BaseItemAdmin.search_fields + ( 'audio_file', )

    def get_fieldsets( self, request, obj=None ):
        rv = super().get_fieldsets( request, obj )
        user = request.user

        new_rows = [
            ('audio_file',),
            '_poster',
            'html3',
            ]

        rv[ self.fs_content ][1]['fields'][0:0] = new_rows

        if user.access_root:
            rv[ self.fs_content ][1]['fields'].insert( 1, ('audio_file_bytes',))
        return rv

    def display_name( self, obj ):
        return obj.audio_file_name
    display_name.short_description = "File Name"

    def display_mb( self, obj ):
        return obj.audio_file_mb
    display_mb.short_description = "File Size"


class AudioRootAdmin( AudioBaseAdmin ):
    list_display = AudioBaseAdmin.list_display + ( '_file', )
    def _file( self, obj ):
        return obj.audio_file.name

root_admin.register( Audio, AudioRootAdmin )


class AudioStaffAdmin( StaffAdminMixin, AudioBaseAdmin ):
    pass

staff_admin.register( Audio, AudioStaffAdmin )
