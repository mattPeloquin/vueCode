#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    MPF logger and log record override
"""
import sys
from numbers import Number
from logging import Logger
from logging import LogRecord

from django.conf import settings

from ..utils.strings import safe_unicode


class mpLogger( Logger ):
    """
    Setup logging to use MPF record
    """

    def makeRecord( self, name, level, fn, lno, msg, args, einfo,
                func=None, extra=None, sinfo=None):
        rv = mpLogRecord( name, level, fn, lno, msg, args, einfo, func, sinfo )
        if extra is not None:
            for key in extra:
                rv.__dict__[ key ] = extra[ key ]
        return rv

class mpLogRecord( LogRecord ):

    def getMessage( self ):
        """
        Format logging message
        """
        rv = self.msg
        try:
            rv = str( rv )
            if self.args:
                args = tuple([
                    arg if isinstance( arg, Number  ) else safe_unicode( arg )
                    for arg in self.args
                    ])
                rv = rv % args

        except Exception as e:
            rv = "ERROR LOGGING {} -> {}, {}".format( safe_unicode( e ),
                        safe_unicode( self.msg ), safe_unicode( self.args ) )
            if settings.DEBUG or settings.MP_TESTING:
                print( rv )
            if settings.MP_TESTING:
                sys.exit("Error creating log string")

        # Sanity check length to limit DoS attack
        return rv[:4000]
