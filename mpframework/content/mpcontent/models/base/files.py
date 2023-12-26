#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared code for file content
"""
from django.db import models

from mpframework.common.cache import stash_method_rv
from mpframework.common.model.fields import mpFileFieldProtected
from mpframework.common.utils.file import reverse_orig_name
from mpframework.common.utils.file import file_size_mb


def create_mpfile_mixin( name, required=False, dbname=None ):
    """
    Factory to create mpfile fields and spporting methods as a class mixin
    """
    blank = not required
    dbname = dbname or name

    # File on S3 under provider folder; no path, but with unique ID
    _file = mpFileFieldProtected( direct=True, mpfile=True,
                blank=blank, null=blank,
                db_column=dbname )
    _file_bytes = models.IntegerField( blank=True, null=True,
                db_column= dbname + '_size' )

    @property
    @stash_method_rv
    def _file_mb( self ):
        # String version of size in MB
        return file_size_mb( getattr( self, name + '_bytes' ) )

    @property
    @stash_method_rv
    def _file_name( self ):
        # Return the original filename without version
        return reverse_orig_name( getattr( self, name ).name )

    return type( 'mpFileMixin_' + name, ( models.Model ,), {
       '__module__': getattr( models.Model, '__module__' ),
       'Meta': type( 'Meta', ( object ,), { 'abstract': True } ),
        name: _file,
        name + '_bytes': _file_bytes,
        name + '_mb': _file_mb,
        name + '_name': _file_name,
        })


class FileContentMixin( create_mpfile_mixin(
            'content_file', dbname='filename' ) ): # TBD DB
    """
    Base support for protected single-file content

    Files have no notion of versions that are tied to user use;
    the last version of a file that was uploaded is what is available.
    """

    # New action types
    ACTION_ATTACHMENT = (
        ( 'action_download', u"Download" ),
        )

    class Meta:
        abstract = True

    access_type = 'download'
    content_fields = ['content_file']

    def save( self, *args, **kwargs ):
        self.update_content_rev()
        super().save( *args, **kwargs )

    @property
    @stash_method_rv
    def protected_storage_path( self ):
        return self.provider.policy.get( 'storage.files',
                    self.provider.protected_storage_path )

    def get_access_url( self, request, **kwargs ):
        """
        Support attachment option for file download
        """
        path = self.content_file.url if self.content_file else None
        if path:
            kwargs['data'] = path
            # Force attachment content-disposition if selected
            if self.access_action in ( 'action_download', ):
                kwargs['attachment'] = self.content_file_name
            return super().get_access_url( request, **kwargs )
