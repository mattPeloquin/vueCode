#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Live event
"""
import re
from django.db import models
from django.conf import settings

from mpframework.common import log
from mpframework.common import constants as mc
from mpframework.common.cache import stash_method_rv
from mpframework.common.utils import now
from mpframework.common.utils import timedelta_past
from mpframework.common.utils import timedelta_future
from mpframework.content.mpcontent.models import BaseItem
from mpframework.content.mpcontent.models import ItemManager
from mpframework.content.mpcontent.models.base.files import create_mpfile_mixin
from mpextend.content.proxy.models import ProxyModelMixin
from mpextend.content.video.models import VideoMixin


_FileMixin = create_mpfile_mixin('event_recording')


class LiveEvent( _FileMixin, VideoMixin, ProxyModelMixin, BaseItem ):
    """
    A perishable live event hosted on an external platform.
    Primarily for wrapping external links with some protection. Also
    supports expiration and upload of a recording.

    Information for joining the event is treated as protected content,
    so is only shown to licensed users when available.

    There is a simple time flow of 'before', 'opened', 'closed'.
    _available is used as event start time, with minute modifiers used to
    define time windows. Different templates display the event for each flow,
    and may be overridden.
    Specific meeting time for an ICS invite is also supported.

    FUTURE - automated support for recurrence
    FUTURE - A true proxy is unlikely to work or be desireable with many platforms,
    so although Proxy functionality is option, primarily expecting direct links.
    """

    # Configuration for different event options
    LIVE_TYPES = tuple( ( k, v['name'] ) for k, v in
                            sorted( settings.MP_CONTENT['LIVE_TYPES'].items() ) )
    event_type = models.CharField( max_length=16, choices=LIVE_TYPES,
                                   default=LIVE_TYPES[0][0], blank=False )

    # Store text or HTML for the event's invite, from another site
    invite_html = models.TextField( blank=True )

    # Common setup info for meetings that can be used for specialized
    # links or along with proxy_main
    event_id = models.CharField( max_length=mc.CHAR_LEN_UI_LONG, blank=True )
    event_account = models.CharField( max_length=mc.CHAR_LEN_UI_LONG, blank=True )
    event_password = models.CharField( max_length=mc.CHAR_LEN_UI_LONG, blank=True )

    # Optional length of event from start, used for default length and meeting invites
    minutes_length = models.IntegerField( blank=True, null=True )
    # Optional window around available datetime for users to join live event
    # Mintues BEFORE _available that users can access the link, allows
    # viewing the event information before it starts
    minutes_open = models.IntegerField( blank=True, null=True )
    # Minuts after start that users can access 'opened' event information
    minutes_close = models.IntegerField( blank=True, null=True )

    class Meta:
        app_label = 'mpcontent'
        verbose_name = u"Event"

    objects = ItemManager()

    access_type = 'event'

    # Changes to any of these fields will trigger cache invalidation
    content_fields = [ 'event_type', '_available', 'event_invite',
            'event_id', 'event_account', 'event_password',
            'minutes_length', 'minutes_open', 'minutes_close',
            'proxy_main', 'event_recording' ]

    def _type_name_LiveEvent( self ):
        # DOWNCAST METHOD
        return self._meta.verbose_name_raw

    def _can_complete_LiveEvent( self ):
        # DOWNCAST METHOD
        return True

    def _type_view_LiveEvent( self, request=None ):
        # DOWNCAST METHOD
        return 'event'

    def save( self, *args, **kwargs ):
        """
        Perform any pre-save fixups based on selected type
        """
        config = self.event_config

        # Set action to match any configuration
        self._action = config.get('action') or ''

        # Run any content fixups
        for fixup in config.get('fixups', []):
            getattr( self, fixup )()

        super().save( *args, **kwargs )

    def access_data( self, request, **kwargs ):
        rv = super().access_data( request, **kwargs )
        rv.update({ 'play_type': 'video' })
        return rv

    @property
    def event_config( self ):
        """
        Return the configuration dict for the selected type
        """
        try:
            return settings.MP_CONTENT['LIVE_TYPES'][ self.event_type ]
        except Exception:
            log.warning("Event type not in configuration: %s", self.event_type)
            return {}

    @property
    @stash_method_rv
    def proxy_options( self ):
        """
        Return options for the type combined with any additional options
        """
        rv = self.event_config.get( 'proxy_options', {} )
        rv.update( super().proxy_options )
        return rv

    # Define event start/stop separate of before/open/closed
    @property
    def event_starts( self ):
        return self._available
    @property
    def event_ends( self ):
        """
        Pick a default for calendar if event length not defined, to allow
        a placeholder to be added.
        """
        length = self.event_length or 60
        return timedelta_future( self._available, minutes=length )

    @property
    @stash_method_rv
    def available( self ):
        """
        Set availability to include open window
        """
        if self._available:
            open_min = self.minutes_open or 0
            return timedelta_past( self._available, minutes=open_min )

    @property
    @stash_method_rv
    def close_datetime( self ):
        """
        After close only the close page is shown.
        Returns None if there is no close date.
        """
        if self._available and self.open_length:
            return timedelta_past( self._available, minutes=self.open_length )

    def is_before( self, _now=None ):
        if self._available:
            _now = _now or now()
            return _now < self.available

    def is_open( self, _now=None ):
        if not self._available:
            return True
        _now = _now or now()
        return _now >= self.available

    def is_active( self, _now=None ):
        return self.is_before( _now ) or self.is_open( _now )

    def is_closed( self, _now=None ):
        if self._available and self.open_length:
            _now = _now or now()
            return _now >= self.close_datetime

    @property
    def is_proxy( self ):
        """
        Is the event a full proxy, or just a page to show invite info?
        """
        return bool( self.proxy_main )

    @property
    def open_length( self ):
        return self.minutes_close or self.minutes_length
    @property
    def event_length( self ):
        return self.minutes_length or self.minutes_close


    @property
    def has_recording( self ):
        """
        Has a separate file of event been uploaded?
        """
        return bool( self.event_recording )

    @property
    @stash_method_rv
    def protected_storage_path( self ):
        return self.provider.policy.get( 'storage.event',
                                         self.provider.protected_storage_path )

    def sources( self, request ):
        """
        Provide protected urls in HTML 5 video tag source attributes
        """
        return [ self.get_source( self.event_recording,
                                    request, "Recording", 'video' ) ]

    """
    Fixup Functions
    These functions perform actions to content. They are called based on
    the configuration settings for each type.
    """

    def fixup_links_in_tabs( self ):
        """
        For embedded links, make their target open in a new tab if
        this has not been done already.
        """
        invite = self.invite_html
        replacements = []
        for m in re.finditer( _anchor_match, invite ):
            link = m.group(1)
            if not _target_match.search( link ):
                replacements.append( ( m.group(1),
                        m.group(2) + ' target="_blank" ' + m.group(3) ) )
        for replacement in replacements:
            invite = invite.replace( replacement[0], replacement[1] )
        self.invite_html = invite

_anchor_match = re.compile( r'((<a.*?)(.*?>))', re.IGNORECASE )
_target_match = re.compile( r'\btarget\s*=', re.IGNORECASE )
