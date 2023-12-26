#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    JSON utilities
"""
import json
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder

from .. import log


TRANSLATE_CHARS = {
    '&': '\\u0026',
    '<': '\\u003c',
    '>': '\\u003e',
    '\u2028': '\\u2028',
    '\u2029': '\\u2029',
    }


def json_dump( data, expand=True, **kwargs ):
    """
    Add error handling and model introspection to MPF serializations
    """
    rv = '{}'
    encoder = DefaultEncoder if expand else CompactEncoder
    try:
        rv = json.dumps( data, cls=encoder, **kwargs )

        for char, repl in TRANSLATE_CHARS.items():
            rv = rv.replace( char, repl )

    except Exception:
        log.exception("JSON DUMP ERROR: %s", data)
        if settings.MP_DEV_EXCEPTION:
            raise
    return rv

# Handlers are called if types not found

class DefaultEncoder( DjangoJSONEncoder ):
    def default( self, obj ):

        # Expand model contents
        from ..model import BaseModel
        if isinstance( obj, BaseModel ):
            return obj.json()

        return super().default( obj )

class CompactEncoder( DjangoJSONEncoder ):
    def default( self, obj ):

        # Just provide ID for models
        from ..model import BaseModel
        if isinstance( obj, BaseModel ):
            return '{{ {}: {} }}'.format( obj.get_django_ctype(), obj.pk )

        return super().default( obj )
