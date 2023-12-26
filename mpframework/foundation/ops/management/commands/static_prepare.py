#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Piggyback on Sass command to prep static files prior to compression
"""
import os
from django.conf import settings
from django.core.files.base import ContentFile
from sass_processor.management.commands.compilescss import Command as SassCommand

from mpframework.common import log
from mpframework.common.deploy.paths import home_path
from mpframework.common.utils import join_paths

from ..utils import template_file_write


# File extensions that will be processed
SASS_EXTENSIONS = ['sass', 'scss']

# Template files that will be processed, and resulting file type
TEMPLATE_TYPES = [
    ( 'html', 'htm' ),
    ]


class Command( SassCommand ):
    """
    Override sass to just do offline compression for folder and file locations
    Forcing offline compression even in local dev environments was the
    best fit for MPF vs. using dynamic compilation in the
    templates for debug scenarios.
    """

    def __init__( self ):

        super().__init__()

        # Only look for sass tags in chtml files as compressed load
        # files will be the only place sass will be included
        self.template_exts = ['.chtml']

    def handle( self, *args, **options ):
        """
        Complete override of sass to just compile known locations directly
        instead of searching python and template files.
        """
        self.handle_templates( *args, **options )
        self.handle_sass( *args, **options )


    def handle_sass( self, *args, **options ):
        log.info("Processing sass files: %s", str(options) )
        self.processed_files = []

        # Required initialization for sass processor class
        self.verbosity = int(options['verbosity'])
        self.sass_precision = options.get( 'sass_precision',
                    getattr( settings, 'SASS_PRECISION', None ))

        # Go through platforms from root backwards, only processing
        # the first of each CSS file
        already_processed = []
        for folder in reversed( settings.MP_PLATFORMS ):
            folder = home_path( folder, 'static', 'mpf-css' )
            for current_folder, _, files in os.walk( folder ):
                for name in files:
                    if( not name.startswith('_') and
                            not ( name in already_processed ) and
                            any( name.endswith(ext) for ext in SASS_EXTENSIONS ) ):
                        path = join_paths( current_folder, name )
                        self.compile_sass( path )
                        already_processed.append( name )

    def save_to_destination( self, content, filename, sass_fileurl ):
        """
        Force output directly into local deployment location.
        MPF uses compressor to wrap up final files and push to S3.
        """
        basename, _ = os.path.splitext( os.path.basename( filename ) )
        destpath = join_paths( 'mpf-css',
                    '{}-{}.css'.format( basename, settings.MP_CODE_CURRENT ) )
        self.storage.delete( destpath )

        # Need to encode to bytes before sending to S3Storages
        content_file = ContentFile( content.encode('utf-8') )
        final_name = self.storage.save( destpath, content_file )
        log.info("Saved: %s", final_name)

    def parse_source( self, filename ):
        log.debug("Parsing: %s", filename)
        super().parse_source( filename )

    def parse_template( self, template_name ):
        log.debug("Parsing: %s", template_name)
        super().parse_template( template_name )

    def compile_sass( self, filename, url='' ):
        log.debug("Compiling: %s -> %s", filename, url)
        super().compile_sass( filename, url )


    def handle_templates( self, *args, **options ):
        """
        Find all template files under static and process them
        """
        log.info("Processing static templates")
        for folder in settings.MP_PLATFORMS:
            folder = home_path( folder, 'static' )
            for current_folder, _, files in os.walk( folder ):
                for name in files:
                    for ttype in TEMPLATE_TYPES:
                        if name.endswith( ttype[0] ):
                            self._handle_file( current_folder, name, ttype )

    def _handle_file( self, folder, name, ttype ):

        # Pass name without extension to template file
        name = '.'.join( name.split('.')[:-1] )

        context = settings.TEMPLATE_OFFLINE_CONTEXT.copy()
        context.update({
            'settings': settings
            })

        file_name = template_file_write( folder, name, ttype[0], ttype[1], context )

        log.info("Saved:  %s", file_name)
