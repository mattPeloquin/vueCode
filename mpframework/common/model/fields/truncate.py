#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Truncated character field

    Can be used for robustness with data that grows programatically
    and WHERE TRUNCATING ISN'T A CONCERN (e.g., aging out old log lines)
"""
from django import forms
from django.db import models

from ... import log
from ... import CHAR_LEN_DB_SEARCH


class TruncateCharFormField( forms.CharField ):
    """
    Truncate value returned from forms to avoid form error handling
    """
    widget = forms.Textarea

    def to_python( self, value ):
        return _truncate_value( value, self.max_length, self.label )


class TruncateCharField( models.CharField ):
    """
    Truncate value to max_length before saving to prevent database exceptions
    An error is logged as this isn't something that should happen; the
    point of this field is robustness, code should still check and manage
    the length of items before they are stored.
    """

    def __init__( self, *args, **kwargs ):
        # Ensure a max length is set of the django field
        kwargs['max_length'] = kwargs.get( 'max_length', CHAR_LEN_DB_SEARCH )
        super().__init__( *args, **kwargs )

    def formfield( self, **kwargs ):
        # Transfer the max length for this model over to form field
        # by copying the class
        form_field_class = type( 'TCFormField', ( TruncateCharFormField, ), {} )
        form_field_class.max_length = self.max_length
        kwargs['form_class'] = form_field_class
        return super().formfield( **kwargs )

    def get_prep_value( self, orig_value ):
        value = super().get_prep_value( orig_value )
        return _truncate_value( value, self.max_length, self.name )


def _truncate_value( value, max_length, _name ):
    if value and len(value) >= max_length:
        value = u"{}...<old removed>".format( value[ :max_length - 20 ] )
        log.debug("TruncateCharField: %s -> %s", _name, len(value))
    return value
