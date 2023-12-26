#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Django App extensions
"""
from django.conf import settings
from django.apps import AppConfig


class mpAppConfig( AppConfig ):

    def __init__( self, *args, **kwargs ):
        super().__init__( *args, **kwargs )
        self.mp_ready_run = False

    def mp_ready( self ):
        """
        Override mp_ready to run ready code once for app stacks and testing
        """
        pass

    def ready( self ):
        if not self.mp_ready_run and (
                settings.MP_TESTING or not settings.MP_IS_COMMAND ):
            self.mp_ready_run = True
            self.mp_ready()
