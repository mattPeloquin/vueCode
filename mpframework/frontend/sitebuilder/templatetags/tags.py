#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Misc template tag support, included by default
"""
from django import template
from django.utils.safestring import mark_safe

from mpframework.common.utils import json_dump


register = template.Library()


@register.simple_tag
def get_json( obj, key, default='{}' ):
    """
    Safe lookup into object or dict with return of json string
    or default string (which should be json).
    """
    try:
        value = obj[ key ]
    except Exception:
        value = getattr( obj, key, None )
    if value is None:
        return default
    return mark_safe( json_dump( value ) )

@register.simple_tag
def to_list( *args ):
    """
    Covert positional args into a list to support using template loops
    on names that should be defined in the template itself.

    {% to_list 'featured' 'core' 'custom1' as areas %}
    """
    return args
