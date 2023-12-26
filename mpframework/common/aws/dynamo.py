#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared Dynamo code
"""
from django.conf import settings

from .. import log
from . import get_resource


def get_dynamo():
    return get_resource('dynamodb')

def get_dynamo_table( table_name ):
    rv = None
    if settings.MP_CLOUD:
        rv = get_dynamo().Table( f'{ settings.MP_PLAYPEN }_{ table_name }' )
        if not rv:
            log.info2("DYNAMO - could not load table: %s", table_name)
    return rv
