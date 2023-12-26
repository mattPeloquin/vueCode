#--- Mesa Platform Framework
"""
    Add HTML5 and parsley attributes as Django forms are generated.

    PORTIONS ADAPTED FROM OPEN SOURCE:
        https://github.com/agiliq/Django-parsley
"""
from django import forms

from ..widgets import mpSelectMultiple


FIELD_ATTRS = [
    ( 'min_length', 'minlength' ),
    ( 'max_length', 'maxlength' ),
    ( 'min_value', 'min' ),
    ( 'max_value', 'max' ),
    ]


def parsleyfy( klass ):
    """
    Adds data-* attributes to form.fields upon form creation

    This allows forms that have parsley validate attribute to
    validate fields as per their type
    """
    old_init = klass.__init__

    def new_init( self, *args, **kwargs ):
        old_init( self, *args, **kwargs )

        # First check every field for parsley additions
        for _, field in self.fields.items():

            if _skip_widget( field.widget ):
                continue

            # Global values for all fields
            attrs = field.widget.attrs
            attrs.update({
                    'data-parsley-trigger': "change focusin focusout",
                    })
            if field.required:
                attrs.update({ 'required': '' })

            # Set attributes for parsley based on Django field attributes
            for attr, name in FIELD_ATTRS:
                value = getattr( field, attr, None )
                if value:
                    attrs[ name ] = value
                    error_message = field.error_messages.get( attr )
                    if error_message:
                        attrs[ 'data-parsley-{}-message'.format( name ) ] = error_message

            # For numbers, HTML5 number only allows integers, which has
            # messed up parsley. Rolled own for decimals, and set type
            # to number for fields to bring up number keypad on mobile
            # Note decimal and float inherit from integer, so check first
            if isinstance( field, forms.DecimalField ) or isinstance( field, forms.FloatField ):
                attrs.update({ 'step': 0.01, 'min': 0.0 })
                field.widget.input_type = 'number'
            if isinstance( field, forms.IntegerField ):
                field.widget.input_type = 'number'

            # Add validation for fields with regex restrictions
            if isinstance( field, forms.SlugField ):
                attrs.update({ 'pattern': '[^\s/\\|+!%{}()\[\]]+' })
            if isinstance( field, forms.RegexField ):
                attrs.update({ 'pattern': field.regex.pattern })

        # Next add any additional custom parsely attributes
        extras = getattr( self, 'parsley_extras', {} )
        for field_name, data in extras.items():
            for key, value in data.items():
                attrs = self.fields[ field_name ].widget.attrs
                if key == 'equalto':
                    # Use HTML id for data-equalto
                    attrs['data-parsley-equalto'] = '#' + self[value].id_for_label
                else:
                    attrs['data-parsley-%s' % key] = value

    klass.__init__ = new_init
    return klass


def _skip_widget( widget ):

    # Don't add to hidden fields
    if isinstance( widget, forms.widgets.HiddenInput ):
        return True

    # Skip admin filter select field since it confuses parsley
    if isinstance( widget, mpSelectMultiple ):
        return True
