#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Dev server WSGI support
"""
from django.conf import settings
from django.core.servers.basehttp import WSGIRequestHandler

from .. import log


class LocalWSGIRequestHandler( WSGIRequestHandler ):
    """
    Request handler that directs HTTP output to logging
    """
    show_all = log.debug_on() > 1

    def parse_request( self ):
        """
        Support skipping some requests from client, as with nginx
        """
        request_line = str( self.raw_requestline )
        for phrase in [
                '/jsi18n/',
                ]:
            if phrase in request_line:
                log.debug2("Skipping: %s", self.raw_requestline)
                return False

        return super().parse_request()

    def log_message( self, format, *args ):
        """
        Special dev server logging
        """

        # Put noisy stuff into sub logging
        if not self.show_all and any( phrase in self.path for phrase in [
                    settings.STATIC_URL,
                    ]
                ):
            log.detail3( format % args )
        else:
            log.info( format % args )
            log.info("%s", "-" * 30 )
