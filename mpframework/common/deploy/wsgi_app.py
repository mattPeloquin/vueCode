#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Django WSGI application handler
"""
import django
from django.conf import settings
from django.core.handlers.wsgi import WSGIHandler

from ..db import db_connection_retry


class mpWSGIHandler( WSGIHandler ):
    """
    Application handler overrides for MPF
    """

    @db_connection_retry
    def make_view_atomic( self, view ):
        """
        HACK - WRAPPING ALL WSGI CALLS
        Django doesn't have a way to wrap all calls to views, so taking
        over the internal make_view_atomic which wraps every view
        for transaction options.
        """
        return super().make_view_atomic( view )

def get_mpwsgi_application():
    django.setup( set_prefix=False )
    return mpWSGIHandler()

if settings.MP_DEVWEB:
    dev_app = get_mpwsgi_application()
