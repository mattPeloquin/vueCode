#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    static_compress wrapper
"""
from django.conf import settings
from compressor.management.commands.compress import Command as CompressCommand

from mpframework.common import log


class Command( CompressCommand ):
    """
    Override compress to only run when option is set true
    and look in chtml files
    """

    def handle( self, *args, **options ):

        if settings.COMPRESS_ENABLED:
            log.info("Compressing static: %s -> %s",
                settings.COMPRESS_STORAGE, settings.COMPRESS_ROOT )

            # Only look for compression tags in chtml files
            options['extensions'] = ['chtml']
            options['force'] = [ True ]

            super().handle( *args, **options )

        else:
            log.info("Compress not enabled -- skipping static file compression")
