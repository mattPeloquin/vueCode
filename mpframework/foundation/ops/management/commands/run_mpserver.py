#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Override Django development server to add support for:

     -- Logging HTTP events through MPF logging
     -- Always using insecure option to support local testing of compressed files
     -- Forces daemon threads to avoid hanging on restart
"""
import socketserver
from django.core.servers.basehttp import WSGIServer

from mpframework.common.deploy.wsgi import LocalWSGIRequestHandler


# Create a version of basehttp.run that uses MPF logging request handler
# and forces daemon threading
def _run( addr, port, wsgi_handler, **kwargs ):
    server_address = (addr, port)
    server_cls = kwargs.pop('server_cls', WSGIServer)
    threading = kwargs.pop('threading', False)
    ipv6 = kwargs.pop('ipv6', False)

    if threading:
        print("MP SERVER MULTITHREADED")
        httpd_cls = type(str('WSGIServer'), (socketserver.ThreadingMixIn, server_cls), {})
    else:
        print("MP SERVER SINGLE THREAD")
        httpd_cls = server_cls

    # Set server to use MPF logging server
    httpd = httpd_cls( server_address, LocalWSGIRequestHandler, ipv6=ipv6 )

    # Set daemon threading so dev server doesn't wait for threads to close,
    # to avoid some hanging situations
    httpd.daemon_threads = True

    httpd.set_app( wsgi_handler )
    httpd.serve_forever()

# MONKEY PATCH basehttp to use the _run defined above
from django.core.servers import basehttp
basehttp.run = _run

# Import StaticRunServer AFTER the monkey patch
# Then define command to call the parent's inner_run, which calls basehttp.run
# Since overrode basehttp before import, inner_run now points to MPF _run
from django.contrib.staticfiles.management.commands.runserver import Command as RunServer

class Command( RunServer ):

    def handle( self, *args, **options ):

        # Forcing insecure serving allows local testing of compressed files, by
        # serving them from the local work static folder
        options.update({ 'insecure_serving': True })

        super().handle( *args, **options )
