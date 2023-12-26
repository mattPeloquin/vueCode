#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared code for items that use HTML video element/palyers
"""
from django.db import models

from mpframework.common import log
from mpframework.common.delivery import use_open
from mpframework.common.model.fields import mpImageField
from mpframework.common.utils.paths import path_extension
from mpframework.content.mpcontent.delivery import create_access_url
from mpextend.user.usercontent.models import UserItem


class VideoMixin( models.Model ):
    """
    Add to classes that use video player (video, audio)
    """

    # Optional display before video starts
    _poster = mpImageField( blank=True, null=True, db_column='poster' )

    class Meta:
        abstract = True

    TYPE_LOOKUP = {}

    def get_source( self, video_file, request, label, display_type ):
        if not video_file:
            return
        url = video_file.url
        ext = path_extension( url )
        file_type = self.TYPE_LOOKUP.get( ext, ext ) if ext else ''
        url = create_access_url( request, 'download', url,
                                 content_rev=self.content_rev )
        return {
            'url': url,
            'label': label,
            'content_type': '{}/{}'.format( display_type, file_type )
            }

    def access_data( self, request, **kwargs ):
        """
        Return dict of urls for use in video player
        """
        sources = self.sources( request )
        normal = sources[0] if sources else {}
        compat = self.compat( sources, normal )
        return {
            'default_url': normal.get( 'url', '' ),
            'poster_url': self.poster_url,
            'player_sources': sources,
            'compatibility_url': compat.get( 'url', '' ),
            }

    def compat( self, _sources, normal ):
        """
        Override to provide a compatibility URL
        """
        return normal

    @property
    def poster_url( self ):
        return self._poster.url

    def _type_view_VideoMixin( self, request=None ):
        """
        Return name for type view based on video parameters
        """
        if self.sb_options['video_test']:
            return 'video_test'
        if self.sb_options['video_native']:
            return 'video_native'

        mode = self.sb_options['access.delivery_mode']
        if request:
            _open = use_open( request.user.delivery_mode( mode ) )
        else:
            _open = use_open( mode )
        if _open:
            return 'video_open'

        return 'video'
