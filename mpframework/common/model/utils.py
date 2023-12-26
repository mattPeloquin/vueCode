#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Field name utils specific to Django apps
"""

from .. import log


def field_names( obj ):
    """
    Wrap Django meta to return field names, including reverse lookups
    """
    return [ f.name for f in obj._meta.get_fields() ]

def data_fields( obj, exclude_relationships=True, includes=None, excludes=None ):
    """
    Returns "data" fields for a model
    This excludes the id field and any reverse lookup and many-to-many fields
    """
    rv = []
    excludes = [ 'id' ] + ( excludes or [] )
    includes = includes or []

    type_exclude = [
        'auto_created',
        'one_to_one',  # Exclude as these are normally setup once during creation
        'one_to_many', # Don't work directly with reverse relationships
        ]

    if exclude_relationships:
        type_exclude += [ 'many_to_many', 'is_relation' ]

    for f in obj._meta.get_fields():
        if f.name in includes or not (
                f.name in excludes or
                    any( getattr( f, attr ) for attr in type_exclude )
                ):
            rv.append( f )

    return rv

def create_filter_kwargs( model, filter_string, value ):
    """
    Returns a kwargs dict intended to be used in a filter statement
    if the filter string is valid for the model
    """
    fields = field_names( model )

    field_to_filter = filter_string.split('__')[0]
    assert field_to_filter

    if field_to_filter in fields:
        return { filter_string: value }
