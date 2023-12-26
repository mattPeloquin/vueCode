#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    FUTURE - update to use per-sandbox localization
"""
import datetime
from django import forms
from django.db import models


class mpDateTime( datetime.datetime ):
    """
    Override Python DateTime with second precision.
    """

    def __new__( cls, *args, **kwargs ):
        if isinstance( args[0], datetime.datetime ):
            dt = args[0]
            return datetime.datetime.__new__( cls,
                        dt.year, dt.month, dt.day,
                        dt.hour, dt.minute, dt.second,
                        0, dt.tzinfo )
        else:
            return datetime.datetime.__new__( cls, *args, **kwargs )

    def __str__( self ):
        return self.strftime('%Y-%m-%d %H:%M')

class mpDateTimeFormField( forms.SplitDateTimeField ):

    def clean( self, value ):
        """
        Allow time to be left blank, in which case it defaults to 0
        """
        if value[0] and not value[1]:
            value[1] = '00:00'
        return super().clean( value )

class mpDateTimeField( models.DateTimeField ):

    def __init__( self, *args, **kwargs ):
        super().__init__( *args, **kwargs )

    def formfield( self, **kwargs ):
        kwargs['form_class'] = mpDateTimeFormField
        return super().formfield( **kwargs )

    def to_python( self, value ):
        dt = super().to_python( value )
        return mpDateTime( dt ) if dt else dt

    def from_db_value( self, value, *args ):
        return self.to_python( value )
