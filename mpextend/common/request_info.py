#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Request info utilities
"""
import requests
from django.conf import settings

from mpframework.common import log
from mpframework.common import constants as mc
from mpframework.common.cache import cache_rv
from mpframework.common.utils.strings import safe_unicode


"""-----------------------------------------------------------------------
    IP info support
    This code is based on data/interface for IP_INFO_API service
"""

def is_threat( ip, cache_only=False ):
    """
    Returns GeoIp object for the request.
    FUTURE - add throttling that passes off to WAF
    """
    if cache_only:
        ipinfo = get_ip_info_cached( ip )
    else:
        ipinfo = get_ip_info( ip )
    return ipinfo.get('is_threat') or ipinfo.get('is_bogon')

def get_geo_data( ip ):
    """
    Returns GeoIp object for the request.
    """
    return GeoIp( get_ip_info( ip ) )

@cache_rv( keyfn=lambda ip:( ip, 'ipinfo' ),
           cache='persist', buffered='local_medium' )
def get_ip_info( ip ):
    """
    Returns whatever data is available for the IP.
    Caching limits calls to external API service
    """
    rv = { 'ip': str(ip) }
    try:
        info_url = settings.MP_ROOT['IP_INFO_API'].get('URL')
        if info_url:
            # Tell service to provide current EXTERNAL IP in dev
            if settings.MP_TESTING or settings.MP_DEVWEB:
                ip = ''
            log.info2("Getting IP info: %s", ip)

            ipinfo = requests.get( info_url.format( ip ),
                        timeout=settings.MP_ROOT['IP_INFO_API']['TIMEOUT'] )
            rv.update( ipinfo.json() )

    except Exception as e:
        log.info("Error getting IP info: %s -> %s", ip, e)
        if settings.MP_TESTING:
            raise
    return rv

@cache_rv( no_set=True, keyname='get_ip_info',
           keyfn=lambda ip:( ip, 'ipinfo' ),
           cache='persist', buffered='local_medium' )
def get_ip_info_cached( ip ):
    # Only check cache for value previously stored by get_ip_info
    return { 'ip': str(ip) }

class GeoIp:
    """
    Convenience class for GeoIp data that provides extra info and valid values
    for missing/erroneous data.
    """
    def __init__( self, ipinfo=None ):
        self._data = ipinfo or { 'ip': 'unknown' }
    def __str__( self ):
        return self.location
    @property
    def dict( self ):
        return self._data
    @property
    def ip( self ):
        return self._data['ip']
    @property
    def country( self ):
        return self._data.get( 'country', '' )
    @property
    def city( self ):
        return self._data.get( 'city', '' )
    @property
    def region( self ):
        return self._data.get( 'region', '' )
    @property
    def postal( self ):
        return self._data.get( 'postal', '' )
    @property
    def latitude( self ):
        return self._data.get( 'latitude', '' )
    @property
    def longitude( self ):
        return self._data.get( 'longitude', '' )
    @property
    def location( self ):
        """
        Human sstring for GEO data
        """
        rv = ""
        if self:
            try:
                rv = "{} {} {}".format( self.city, self.region, self.country )
            except Exception as e:
                log.info2("Error getting GeoIP location: %s -> %s", self.ip, e)
        return rv

"""-----------------------------------------------------------------------
    Other request info utils
"""

def safe_user_agent( request, max_len=mc.CHAR_LEN_PATH ):
    rv = ""
    try:
        user_data = request.META.get( 'HTTP_USER_AGENT' , "" )
        rv = safe_unicode( user_data[ :max_len ] )
    except Exception:
        log.info2("Tracking user agent error: %s", request.mpipname)
        if settings.MP_TESTING:
            raise
    return rv

@cache_rv( keyfn=lambda ua:( ua, 'deviceinfo' ),
           cache='persist', buffered='local_medium' )
def get_device_info( ua ):
    """
    Returns whatever data is available for the IP.
    Caching limits calls to external API service
    """
    rv = { 'ua': ua }
    try:
        info_url = settings.MP_ROOT['DEVICE_INFO_API'].get('URL')
        if info_url:
            log.info2("Getting Device info: %s", ua)

            info = requests.get( info_url.format( ua ),
                        timeout=settings.MP_ROOT['DEVICE_INFO_API']['TIMEOUT'] )
            rv.update( info.json() )

    except Exception as e:
        log.info("Error getting device info: %s -> %s", ua, e)
        if settings.MP_TESTING:
            raise
    return rv
