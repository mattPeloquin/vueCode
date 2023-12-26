#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared user tracking SQL model

    Some aggregate user and visitor data is stored in SQL along with
    information on recent sessions, IP addresses, and devices that
    is used both programatically and for manual inspection.
    Detailed history of user events is handled in timeseries.
"""
from django.db import models
from pytz import UTC

from mpframework.common import log
from mpframework.common import constants as mc
from mpframework.common.cache import stash_method_rv
from mpframework.common.utils import tz
from mpframework.common.utils import dt
from mpframework.common.utils import now
from mpframework.common.model.fields import YamlField
from mpframework.common.model.fields import mpDateTimeField
from mpframework.common.model.fields import TruncateCharField
from mpextend.common.request_info import GeoIp


class BaseTracking( models.Model ):
    """
    Data and logic for user and visitor tracking
    """

    # Track last use separate from hist_modified
    last_update = mpDateTimeField( db_index=True, default=now )

    # Values for DB sorting or searching
    ip_address = TruncateCharField( db_index=True, blank=True,
                max_length=mc.CHAR_LEN_IP )

    # Dict to store session information
    # Keys are last known sessions keys (check against store to know if active)
    # Values are recent session information for each key
    sessions = YamlField( null=True, blank=True, safe_dict=False )

    # IP and device information
    ips = YamlField( null=True, blank=True, safe_dict=False )
    devices = YamlField( null=True, blank=True, safe_dict=False )

    class Meta:
        abstract = True

    @property
    @stash_method_rv
    def active_sessions( self ):
        """
        Check list of save sessions for active session info
        This only returns current info in the DB
        """
        log.debug2("Getting active sessions: %s", self)
        return [ s for s in self.session_list if s['active'] ]
    @property
    @stash_method_rv
    def session_list( self ):
        return _sorted_from_dict( self.sessions )

    @property
    @stash_method_rv
    def ip_list( self ):
        return _sorted_from_dict( self.ips )
    @property
    @stash_method_rv
    def device_list( self ):
        return _sorted_from_dict( self.devices )

    @property
    def geoip( self ):
        return GeoIp( self.ip_list[0] if self.ip_list else None )
    @property
    def device( self ):
        return self.device_list[0] if self.device_list else None

    @property
    def last_use( self ):
        dt = tz( self.last_update )
        return str( dt.date() )

def _sorted_from_dict( data, time_key='last_time' ):
    """
    Returns list of dict tracking entries from tracking YAML fields
    by last use date with key added.
    """
    rv = []
    for key, value in data.items():
        value['key'] = key
        rv.append( value )

    rv.sort( key=lambda item: dt( item.get( time_key, now() )
                ).replace( tzinfo=UTC ), reverse=True )
    return rv
