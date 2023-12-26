#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Time utils
    MODULE IS * imported by mpframework.common.utils

    Sub-second accuracy is not meaningful for most MPF time
    usage, so are stripped by default.
"""
import time
import datetime
from dateutil import parser
from django.utils import timezone
from django.core.exceptions import ImproperlyConfigured

from .. import log


# Date in the past and future for sorting/compare of date time objects
# to None, where None represents no end, or no start
DATE_PAST = datetime.date( datetime.MINYEAR, 1, 1 )
DATE_FUTURE = datetime.date( datetime.MAXYEAR, 1, 1 )
DATETIME_PAST = datetime.datetime( datetime.MINYEAR, 1, 1 )
DATETIME_FUTURE = datetime.datetime( datetime.MAXYEAR, 1, 1 )


def now( tz=None, use_ms=False ):
    """
    Try to use Django timezone aware datetime, but if it isn't available
    (e.g., in fab utils) then use use normal datetime
    """
    rv = None
    if not tz:
        try:
            rv = timezone.now()
        except ImproperlyConfigured:
            pass
    if not rv:
        rv = datetime.datetime.now( tz )
    assert( rv )
    #if not use_ms:
    #    rv = rv.replace( microsecond=0 )
    return rv

def dt( value ):
    """
    Convert string into datetime if possible
    """
    rv = None
    try:
        if isinstance( value, datetime.datetime ):
            rv = value
        else:
            rv = parser.parse( value )
        rv.replace( microsecond=0 )
    except Exception as e:
        log.info2("CONFIG - ERROR dt: %s", e)
    return rv

def tz( rv ):
    """
    Convert datetimes into current local time
    """
    try:
        return timezone.localtime( rv )
    except Exception:
        return rv

def tz_strip( rv ):
    """
    Strip any timezone knowledge, for use if naive and timezone objects
    need to be compared, and it is not known which is which or if
    naive can be successfully converted to aware
    """
    try:
        return rv.replace( tzinfo=None )
    except Exception:
        return rv

def epoch_ms():
    return int( round( time.time() * 1000 ) )

def timedelta_future( current=None, **kwargs ):
    """
    Return datetime in future
    """
    current = current or now()
    return current + datetime.timedelta( **kwargs )

def timedelta_past( current=None, **kwargs ):
    """
    Return datetime in past
    """
    current = current or now()
    return current - datetime.timedelta( **kwargs )

def timedelta_seconds( delta ):
    """
    Return the total seconds present in a timedelta object
    """
    return (delta.days * 60 * 60 * 24) + delta.seconds

def timedelta_minutes( delta ):
    """
    Return the total minutes present in a timedelta object
    """
    return (delta.days * 60 * 24) + seconds_to_minutes( delta.seconds )

def seconds_to_minutes( seconds ):
    """
    Provide integer minutes that are rounded up
    """
    return ( seconds // 60 ) + 1 if seconds else 0


def timestamp( time=None, fmt='%Y/%m/%d_%H:%M:%S' ):
    """
    Default timestamp strings
    """
    time = time or now()
    return time.strftime( fmt )


def week_incrementor( weeks, label=u"week" ):
    """
    Factory to return method for incrementing week counts
    """
    current = now()
    cutoff = timedelta_past( current, weeks=weeks )

    weeks_count = {}
    for week in range( 1, weeks + 1 ):
        weeks_count[ "{} {}".format( label, week ) ] = 0

    def week_increment( date ):
        if date and date > cutoff:
            diff = current - date
            weeks = (diff.days // 7) + 1
            week = "{} {}".format( label, weeks )
            weeks_count[ week ] = weeks_count.get( week, 0 ) + 1

    return cutoff, weeks_count, week_increment


class ElapsedTime:
    """
    Simple class to track both a total elapsed time and blocks
    of time within the total
    """

    def __init__( self ):
        self._timings = {}
        self.set('START_RUN')

    def elapsed( self ):
        return self.get('START_RUN')

    def set( self, checkpointName='DEFAULT' ):
        self._timings[ checkpointName ] = now( use_ms=True )

    def get( self, checkpointName='DEFAULT' ):
        return now( use_ms=True ) - self._timings[ checkpointName ]
