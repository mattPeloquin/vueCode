#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Debug Middleware - NOT registered unless DEBUG is set
"""
import re

from mpframework.common import log


class mpDebugMiddleware:
    """
    Debug logging and injecting timing info on page
    Can be used for other hack debugging as needed
    """
    def __init__( self, get_response ):
        self.get_response = get_response

    def __call__( self, request ):
        response = self.process_request( request )

        if not response:
            response = self.get_response( request )

        return self.process_response( request, response )


    def process_request( self, request ):
        if not request.is_lite:
            log.timing2("FINISHED REQUEST MIDDLEWARE: %s", request.mptiming)


    def process_response( self, request, response ):
        if request.is_lite:
            return response

        # Is this normal response with content? (e.g., not a streaming response)
        if request.mpinfo.get('response_type') == 'page':
            content = getattr( response, 'content', None )
            if content and hasattr( request, 'mptiming' ):

                # Fixup html in response with timing (if string)
                html = content.decode('utf-8')
                stat_comment = re.compile(r'<!--MPSTATS-->')
                match = stat_comment.search( html )
                if match:
                    stat_html = "<b>Server: %s</b>" % str( request.mptiming )
                    new_html = html[ :match.start() ] + stat_html + html[ match.end(): ]
                    response.content = new_html

            log.timing2("START RESPONSE MIDDLEWARE: %s", request.mptiming)
        return response
