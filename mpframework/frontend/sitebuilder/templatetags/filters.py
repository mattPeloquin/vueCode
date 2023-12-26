#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Misc template tag support, included by default
"""
from django import template
from django.utils.safestring import mark_safe

from mpframework.common.utils.json_utils import json_dump
from mpframework.common.utils.html_utils import sanitize_html

register = template.Library()


@register.filter
def sanitize( text ):
    """
    Use instead of Django safe filter to allow HTML injected into templates
    but clean up security issues AND mistakes like not closing a tag
    which could impact the entire UI.
    """
    return mark_safe( sanitize_html( text ) )

@register.filter
def jsbool( value ):
    """
    Maps django true/false onto Javascript true/false, with special
    accommodation for conversion of None to a string
    """
    return 'true' if value and value != 'None' else 'false'

@register.filter
def json( value ):
    """
    Create JSON in template from dict
    """
    return mark_safe( json_dump( value ) )

@register.filter
def label( value ):
    return mark_safe( value.replace( ":</label>", "</label>" ) )

@register.filter
def get( obj, key ):
    """
    Provide an explicit get that works better than Django 'default' for:
     - Dict gets that default to None, then won't work with default_if_none
     - Names that fail, like 'may not begin with underscores'
        {{ xyz | get:'_member' }}
    """
    try:
        return obj[ key ]
    except Exception:
        return getattr( obj, key, None )

@register.filter
def query_string( text ):
    """
    Convert string for use in query string
    """
    return text.replace(' ', '+').replace('&#61;', '=')

@register.filter
def concat( text1, text2 ):
    return str(text1) + str(text2)

@register.filter
def startswith( text, start ):
    if isinstance( text, str ):
        return text.startswith( start )

@register.filter
def endswith( text, start ):
    if isinstance( text, str ):
        return text.endswith( start )
