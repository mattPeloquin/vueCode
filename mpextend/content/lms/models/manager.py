#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Manager for package class
"""
from django.conf import settings

from mpframework.common import log
from mpframework.foundation.tenant.models.base import TenantManager


class PackageManager( TenantManager ):

    def create_obj( self, **kwargs  ):
        """
        Creates a record that represents an LMS package zip archive. This is tracked
        for each version of the zip uploaded, so tracking information for people
        starting older lessons is maintained.
        The archvie zip file may be uploaded directly to S3 (then file_data is null)
        or stored locally using file_data and then pushed to S3.
        When the package is used it is "mounted" by unizipping the files into a
        folder in the protected S3 bucket.
        """
        kwargs['_provider'] = kwargs['package_root'].provider
        kwargs['run_ready'] = False

        # Archive file name must be passed in (clone) or from file info (form create)
        file_name = kwargs.pop( 'file_name', None )
        file_data = kwargs.pop( 'file_data', None )
        if file_name:
            kwargs['archive_name'] = file_name
        kwargs['run_name'] = self.model._run_name( kwargs['archive_name'] )

        package = self.model( **kwargs )
        package.save()
        log.info2("CREATED PACKAGE: %s", kwargs['archive_name'])

        # Write upload data into local file if it wasn't uploaded directly
        if file_data:
            package.write_archive( file_data )

        # Mount the zip file by unpacking and pushing to S3
        package.mount_archive()

        return package

    def prewarm( self ):
        """
        Warm up protected package location by ensuring protected package files
        are ready to be downloaded. In dev for some testing this is a \
        convenience to decrease test cycle time.

        NOTE -- this can cause race conditions if the PREWARM setting is used
        incorrectly, such as having servers in a cluster all try
        to update an S3 protected location.
        """
        if settings.MP_PROTECTED.get('PREWARM'):
            try:
                for package in self.filter():
                    package._ensure_mounted()
            except Exception:
                # This will fail if DB not in place
                pass
