#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    static_collect is MPFs's collectstatic wrapper
"""
from fnmatch import fnmatch
from django.conf import settings
from django.contrib.staticfiles.management.commands.collectstatic import Command as CollectstaticCommand

from mpframework.common import log
from mpframework.common.utils import path_clean


class Command( CollectstaticCommand ):
    """
    Override collectstatic to ignore folders based on MPF settings
    and fix issue with comparing files on S3

    Depending on profile, limits copying unneeded JS and other files
    to S3/Cloudfront for build speed and S3 versioning cleanliness.

    This is a bit of a mess because it can't be managed easily through
    modifying Django static files configuration, because for MPF
    files that are compressed, the compress process uses the static files
    to find the items to compress.
    """

    def add_arguments( self, parser ):
        """
        Add option for whether files should be found with compression on
        -- to execute MPF build two static passes are needed,
        one that pulls in uncompressed files to work folder to be
        compressed, and another to push compressed files.
        """
        super().add_arguments( parser )
        parser.add_argument(
            '--nocompress', action='store_false', dest='compress',
            default=settings.COMPRESS_ENABLED,
            help="Ignore MPF compress setting when finding files",
        )

    def set_options( self, **options ):
        """
        Override some defaults
        """
        super().set_options( **options )

        # Turn off default logging to use framework's instead
        self.verbosity = 0

        # Build up paths to ignore
        # FUTURE - DJ 2.2 added path detection, so could remove
        self.ignore_paths = []
        self.ignore_paths.extend( settings.MP_DEPLOY_STATIC_IGNORE_ALWAYS )
        if options['compress']:
            self.ignore_paths.extend( settings.MP_DEPLOY_STATIC_IGNORE_COMPRESS )
        self.ignore_patterns += self.ignore_paths

    def copy_file( self, path, prefixed_path, source_storage ):
        """
        Override copy for more control including expanding ignore_patterns
        to include full paths (ignore_patterns only looks at path segments).
        Note this won't work if symlink static is enabled, but that is
        not used with MPF.
        """
        if prefixed_path in self.copied_files:
            return log.debug("Skipping (already copied earlier): %s", path)

        p = path_clean( path )
        for ignore_path in self.ignore_paths:
            if fnmatch( p, ignore_path ):
                log.debug("Skipping (ignore): %s", path)
                return

        # If no replacement needed, don't copy
        if not self.delete_file( path, prefixed_path, source_storage ):
            return

        # Copy to storage
        if self.dry_run:
            log.info("Pretending to copy %s", source_storage.path( path ))
        else:
            with source_storage.open( path ) as source_file:
                log.debug("Static copy: %s -> %s", source_file, prefixed_path)
                self.storage.save( prefixed_path, source_file )
        self.copied_files.append( prefixed_path )


    def delete_file( self, path, target_path, source_storage ):
        """
        Override default delete_file to remove checks on local file
        and symlink when comparing if files have been modified
        """
        if self.storage.exists( target_path ):
            try:
                target_modified = self.storage.get_modified_time( target_path )
            except ( OSError, NotImplementedError, AttributeError ) as e:
                log.info("Target get_modified_time failed: %s -> %s", target_path, e)
            else:
                try:
                    source_modified = source_storage.get_modified_time( path )
                except ( OSError, NotImplementedError, AttributeError ) as e:
                    log.info("Source get_modified_time failed: %s -> %s", path, e)
                else:
                    # Avoid sub-second precision
                    target_modified = target_modified.replace( microsecond=0 )
                    source_modified = source_modified.replace( microsecond=0 )
                    # Skip the file if the source file is younger
                    if target_modified >= source_modified:
                        log.debug("Skipping (not modified): %s ", target_path)
                        if target_path not in self.unmodified_files:
                            self.unmodified_files.append( target_path )
                        return False

            # Then delete the existing file if really needed
            if self.dry_run:
                log.debug("Pretending to delete '%s'" % target_path)
            else:
                log.debug("Deleting '%s'" % target_path)
                self.storage.delete( target_path )

        log.info("Replacing: %s", path)
        return True
