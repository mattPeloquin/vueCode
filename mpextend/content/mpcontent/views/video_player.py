#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Views for content shown in video/audio player
"""
from django.template.response import TemplateResponse

from mpframework.common import log
from mpframework.common.api import respond_api
from mpframework.content.mpcontent.delivery import set_access_response_handler

from ..models import Audio
from ..models import Video


def _video_response_handler( request, access_session ):
    """
    The video access link loads a page with video player along with one
    or more download links in the video source tag.
    The download links will then be downloaded to browser via the
    download response handler.
    """
    item_id = access_session['data']
    video = Video.objects.get( _provider_id=request.sandbox._provider_id,
                                id=item_id )
    log.debug("PROTECTED VIDEO response: %s -> %s", request.mpname, video)
    return _response( video, request )

set_access_response_handler( Video.access_type, _video_response_handler )

def _audio_response_handler( request, access_session ):
    """
    Sets up an audio file in the video player
    """
    item_id = access_session['data']
    audio = Audio.objects.get( _provider_id=request.sandbox._provider_id,
                                id=item_id )
    log.debug("PROTECTED AUDIO response: %s -> %s", request.mpname, audio)
    return _response( audio, request )

set_access_response_handler( Audio.access_type, _audio_response_handler )

def _response( item, request ):
    """
    Expect a content item that duck-types to Video's sources.
    Returns either an API response with the acesss urls or a
    page response that loads a player.
    """

    # Add item, it's content user data, and values that need request
    context = {
        'is_page_content': True,
        'item': item,
        }
    context.update( item.access_data( request ) )

    # For API requests, just return the access url information,
    # used when the player is reused
    if request.is_api:
        return respond_api( context )

    # Otherwise return new page for player
    return _player_response( item, context, request )

def _player_response( item, context, request ):
    """
    Provide page response that will load player based on options
    """
    view_type = item.type_view( request )
    template = _video_templates.get( view_type )
    log.debug("Video player page: %s -> %s, %s",
                request.mpname, template, item)
    return TemplateResponse( request, template, context )

_video_templates = {
    'video': 'content/page/video_videojs.chtml',
    'video_test': 'content/page/video_test.html',
    'video_native': 'content/page/video_native.html',
    'video_open': 'content/page/video_native.html',
    }
