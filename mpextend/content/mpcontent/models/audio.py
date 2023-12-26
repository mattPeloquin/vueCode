#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Protected audio - played through video player
"""

from mpframework.common.cache import stash_method_rv
from mpframework.content.mpcontent.models import BaseItem
from mpframework.content.mpcontent.models import ItemManager
from mpframework.content.mpcontent.models.base.files import create_mpfile_mixin
from mpextend.content.video.models import VideoMixin


_AudioFileMixin = create_mpfile_mixin('audio_file')


class Audio( _AudioFileMixin, VideoMixin, BaseItem ):
    """
    Represents an audio content item, which is a file that can be streamed
    in the video player, with options for player layout and a poster image.
    """
    class Meta:
        app_label = 'mpcontent'
        verbose_name = u"Audio file"

    TYPE_LOOKUP = {
        'm4a': 'mp4',
        }

    access_type = 'audio'

    objects = ItemManager()

    def _type_name_Audio( self ):
        # DOWNCAST METHOD
        return self._meta.verbose_name_raw

    def _can_complete_Audio( self ):
        # DOWNCAST METHOD
        return True

    def _type_view_Audio( self, request=None ):
        # DOWNCAST METHOD
        return self._type_view_VideoMixin( request )

    def access_data( self, request, **kwargs ):
        rv = super().access_data( request, **kwargs )
        rv.update({ 'play_type': 'audio' })
        return rv

    @property
    @stash_method_rv
    def protected_storage_path( self ):
        return self.provider.policy.get( 'storage.audio',
                                         self.provider.protected_storage_path )

    def sources( self, request ):
        """
        Provide protected urls in HTML 5 video tag source attributes
        """
        return [ self.get_source( self.audio_file, request, "Track", 'audio' ) ]
