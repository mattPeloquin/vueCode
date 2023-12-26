#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Autolookup
    Makes calls to server as user types to suggest items
    in select lists.
"""
from django.conf import settings

from mpframework.common import log

from .lookup import Lookup


_ERROR_RESULT_TEXT = u"No results found"


class Autolookup( Lookup ):
    """
    Specialize lookup for MPF model, assuming Select2 consumption
    """

    def get_data( self ):
        limit = int( self.GET.get( 'limit',
                    settings.MP_LOOKUP['AUTO_LIMIT'] ) )
        objs = self.get_queryset()[ :limit ]
        results = [{
                'id': obj.pk,
                'text': str( obj ),
                } for obj in objs ]
        log.debug2("Autolookup: %s -> %s", self.GET, results)
        return results

    def error_data( self ):
        """
        Default error placeholder
        """
        return { 'id': 0, 'text': _ERROR_RESULT_TEXT }
