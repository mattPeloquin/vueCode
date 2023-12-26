#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    MPF base Middleware

    FUTURE - convert middleware from DJ 1.10 style to process_view, etc.
"""

from . import log


class mpMiddlewareBase:
    """
    Allows pre DJ 1.10 process_request, process_response methods
    Adds debug logging based on some knowledge of MPF requests
    """

    def __init__( self, get_response ):
        self.get_response = get_response

    def __call__( self, request ):
        """
        Called by Django middleware handler, provides optional support
        for Django 1.10 middleware methods
        """
        response = None

        if hasattr( self, 'process_request' ):
            response = self.process_request( request )

            log.debug_on() and log.timing3("%s process REQUEST complete: %s",
                                self.__class__.__name__, request.mptiming)

        if not response:
            response = self.get_response( request )

            log.debug_on() and log.timing3("%s get RESPONSE complete: %s",
                                self.__class__.__name__, request.mptiming)

        if hasattr( self, 'process_response' ):
            response = self.process_response( request, response )

            log.debug_on() and log.timing3("%s process RESPONSE complete: %s",
                                self.__class__.__name__, request.mptiming)

        return response
