#--- Mesa Platform, Copyright 2021 Vueocity, LLC

from django.db import models

from ... import log
from ...utils.countries import COUNTRIES


class CountryField( models.CharField ):
    """
    Model field country support

     - Defines 2 letter DB field
     - Sets up common Admin country select choices
     - Allows typing for less common ones
    """
    MAX_LENGTH = 2

    def __init__( self, *args, **kwargs ):
        kwargs.update({
            'blank': True,
            'max_length': self.MAX_LENGTH,
            'choices': COUNTRIES,
            })
        super().__init__( *args, **kwargs )

    def get_internal_type(self):
        return "CharField"

    def get_prep_value( self, orig_value ):
        value = super().get_prep_value( orig_value )
        if value and len( value ) > self.MAX_LENGTH:
            value = ''
            log.debug2("CountryField truncated -- %s: %s -> %s", self.name, orig_value, value )
        return value
