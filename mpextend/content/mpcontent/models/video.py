#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Protected video viewed from the platform

    Video content access links redirect to MPF viewer or
    new page that loads the video player, which is provided a
    SECOND access link that uses 'download' action for file bytes.
"""

from mpframework.common.cache import stash_method_rv
from mpframework.content.mpcontent.models import BaseItem
from mpframework.content.mpcontent.models import ItemManager
from mpframework.content.mpcontent.models.base.files import create_mpfile_mixin
from mpextend.content.video.models import VideoMixin

# TBD DB
_MedFileMixin = create_mpfile_mixin( 'file_med', dbname='filename' )
_LowFileMixin = create_mpfile_mixin('file_low')
_HighFileMixin = create_mpfile_mixin('file_high')


class Video( _LowFileMixin, _MedFileMixin, _HighFileMixin,
                VideoMixin, BaseItem ):
    """
    Represents a video content item, which may be:

        - Single file
        - 2 or more files for low, med, high bitrate

    FUTURE -- support video transcoding, watermarking, DASH transcode, DRM
    """
    class Meta:
        app_label = 'mpcontent'
        verbose_name = u"Video"

    objects = ItemManager()

    access_type = 'video'
    content_fields = [ 'file_med', 'file_high', 'file_low' ]

    def save( self, *args, **kwargs ):
        self.update_content_rev()
        super().save( *args, **kwargs )

    @property
    @stash_method_rv
    def protected_storage_path( self ):
        return self.provider.policy.get( 'storage.video',
                                         self.provider.protected_storage_path )

    def _type_name_Video( self ):
        # DOWNCAST METHOD
        return self._meta.verbose_name_raw

    def _type_view_Video( self, request=None ):
        # DOWNCAST METHOD
        return self._type_view_VideoMixin( request )

    def _can_complete_Video( self ):
        # DOWNCAST METHOD
        return True

    def access_data( self, request, **kwargs ):
        rv = super().access_data( request, **kwargs )
        rv.update({ 'play_type': 'video' })
        return rv

    def sources( self, request ):
        """
        Provide protected urls in HTML 5 video tag source attributes,
        the default should be the first in list.
        """
        rv = []
        sources = {
            1: ( self.file_med, u"Normal" ),
            2: ( self.file_high, u"High" ),
            3: ( self.file_low, u"Low" ),
            }
        for key, ( video_file, name ) in sorted( sources.items() ):
            source = self.get_source( video_file, request, name, 'video' )
            if source:
                rv.append( source )
        return rv

    def compat( self, sources, normal ):
        """
        Override to provide a compatibility URL
        """
        compat = None
        for s in sources:
            if self.file_low and ( s['label'] == 'Low' ):
                compat = s
                break
        return compat or normal
