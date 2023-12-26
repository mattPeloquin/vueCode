#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared logic for access time periods and related usage metering
"""
from dateutil.relativedelta import relativedelta
from django.db import models
from django.conf import settings

from mpframework.common import log
from mpframework.common.utils import now
from mpframework.common.utils import safe_int
from mpframework.common.model.fields import mpDateTimeField


class TimePeriod:
    """
    Helper for mapping/converting programmatic names time names to UI names.
    Assumption is month and year are "same day/date X months/year" from now.
    Access periods focus on minute resolution; seconds are used for some
    conversions, and translating into months/years is approximated.
    """
    MAPPING = {
        # DB, detection, UI, plural, seconds or days conversion,
        # relativedelta/Python names
        '':         ( 'p', u"perpetual", u"perpetual", None, None ),
        'minute':   ( 'mi', u"minute", u"minutes", 60, 'minutes' ),
        'hour':     ( 'h', u"hourly", u"hours", 3600, 'hours' ),
        'day':      ( 'd', u"daily", u"days", 86400, 'days' ),
        'week':     ( 'w', u"weekly", u"weeks", 7, 'weeks' ),
        'month':    ( 'mo', u"monthly", u"months", 30, 'months' ),
        'year':     ( 'y', u"yearly", u"years", 365, 'years' ),
        }
    @classmethod
    def unit_name( cls, unit, plural=False ):
        return cls.MAPPING[ unit ][ 2 if plural else 1 ]
    @classmethod
    def conversion( cls, unit ):
        return cls.MAPPING[ unit ][3]
    @classmethod
    def python_name( cls, unit ):
        return cls.MAPPING[ unit ][4]
    @classmethod
    def choices( cls ):
        return [ (key, val[1]) for (key, val) in cls.MAPPING.items() ]

    @classmethod
    def clean( cls, unit_duration ):
        # Reversible DB string
        return cls.desc( *unit_duration, use_prefix=False )
    @classmethod
    def desc( cls, unit, duration, use_prefix=u"every " ):
        if not unit:
            return cls.unit_name('')
        plural = duration and duration > 1
        prefix = ""
        if plural or unit in [ 'minute' ]:
            prefix = use_prefix or ""
        if plural:
            return "{}{:.0f} {}".format( prefix, duration,
                        cls.unit_name( unit, True ) )
        else:
            return "{}{}".format( prefix, cls.unit_name( unit ) )

    @classmethod
    def unit_and_duration( cls, string ):
        """
        Simple parsing of a string to determine time unit and duration
        for space sparated strings like "3 months", with special casing
        for duration of 1 for yearly, monthly, weekly, daily.
        Returns tuple with:
         - string unit key mapping name and integer duration
         - if only number can be determined, defaults for minutes
         - ('', None) if string is blank or unable to parse
        Yearly is the maximum time duration allowed, except for perpetual,
        since MPF account/license management assumes that simplification.
        """
        unit = ''
        duration = None
        try:
            string = string.strip('"\'').lower()
            if string:
                tokens = string.split(' ')
                tokens = [ t for t in tokens if t ]
                if tokens:
                    # Handle yearly, daily, etc. and minutes default
                    if len( tokens ) == 1:
                        token = tokens[0]
                        if safe_int( token ):
                            duration = abs( int( token ) )
                            unit_str = 'mi'
                        else:
                            duration = 1
                            unit_str = token
                    # Otherwise specific duration
                    else:
                        duration = abs( int( tokens[0] ) )
                        unit_str = tokens[1]
                    # Otherwise specific duration
                    for key, mapping in cls.MAPPING.items():
                        if unit_str.startswith( mapping[0] ):
                            unit = key
                            break
                    if not unit in cls.MAPPING:
                        unit = ''
        except Exception as e:
            log.info2("CONFIG - access_period: %s", string)
            if settings.MP_TESTING:
                raise
        return unit, duration

    @classmethod
    def relative_delta( cls, unit, duration ):
        """
        Return relativedelta object that can be used in calculations,
        or None for perpetual.
        """
        delta_unit = cls.python_name( unit )
        if delta_unit:
            return relativedelta( **{ cls.python_name( unit ): duration } )

    @classmethod
    def relative_duration( cls, unit, duration, new_unit ):
        """
        Convert total duration between units, using relative delta to calculate
        from now for the ambiguous cases. Returns None for perpetual.
        """
        relative_delta = cls.relative_delta( unit, duration )
        if relative_delta:
            ref_time = now()
            time_point = ref_time - relative_delta
            # Crate timedelta object to get seconds
            difference = ref_time - time_point
            # Sometimes approximate conversion back to units
            if new_unit in [ 'week', 'month', 'year' ]:
                diff_duration = difference.days
            else:
                diff_duration = difference.seconds
            return diff_duration // cls.conversion( new_unit )

    @classmethod
    def total_minutes( cls, unit, duration ):
        return cls.relative_duration( unit, duration, 'minute' )


class AccessPeriodMixin( models.Model ):

    # Relative time period for access
    # String with duration and time unit which defines the access period
    # Only used to calculate the end date at start and with each renewal
    _access_period = models.CharField( max_length=12, blank=True,
                                       db_column='access_period',
                                       verbose_name=u"Access period" )

    # Cap on time period
    # If shorter than next access period, cuts the access period short,
    # Otherwise date after which access_period won't be renewed
    access_end = mpDateTimeField( blank=True, null=True )

    class Meta:
        abstract = True

    @property
    def access_period( self ):
        """
        APA can override accessor to implement defaulting to PA
        """
        return self._access_period

    @property
    def access_period_tuple( self ):
        """
        Returns duration and time unit for access period.
        If this instance has a non-blank access period string in DB,
        update it to match programattic unit and duration.
        """
        return TimePeriod.unit_and_duration( self.access_period )

    def clean_period( self ):
        """
        Make saved string match programmatic tuple.
        """
        if self._access_period:
            unit_duration = TimePeriod.unit_and_duration(
                        self._access_period )
            self._access_period = TimePeriod.clean( unit_duration )

    def save( self, *args, **kwargs ):
        self.clean_period()
        super().save( *args, **kwargs )

    @property
    def access_period_minutes( self ):
        """
        Provide exact or approximate total minutes for access period.
        """
        return TimePeriod.total_minutes( *self.access_period_tuple )

    @property
    def access_period_delta( self ):
        """
        Return relativedelta object for agreement period.
        """
        return TimePeriod.relative_delta( *self.access_period_tuple )

    def access_period_desc( self, unit=None, use_prefix=False ):
        """
        Text description for total time in access period, unless ongoing
        """
        try:
            current_unit, duration = self.access_period_tuple
            if unit:
                duration = TimePeriod.relative_duration( current_unit, duration, unit )
            else:
                unit = current_unit
            return TimePeriod.desc( unit, duration, use_prefix )
        except Exception as e:
            log.info2("Access period desc error: %s -> %s, %s", e, self, unit)
            if settings.MP_TESTING:
                raise

    @property
    def metering_desc( self ):
        rv = ""
        points = self.rules['unit_points']
        users = self.rules['unit_users']
        minutes = self.rules['unit_minutes']
        if points: rv += u"{} pts ".format( points )
        if users: rv += u"{} users ".format( users )
        if minutes: rv += u"{} mins".format( minutes )
        return rv
