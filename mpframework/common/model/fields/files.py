#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Tenant-aware file field handling for mpFramework

    All file uploads flow through here for both public and protected files.
    MPF stores every file upload as a unique, one-time event.
    Old files (created up new uploads for the same DB item) are abandoned
    and are cleaned up by garbage bots.

    FUTURE - override Django 100 char limit on image file names, or ensure names won't go over limit
"""
from django.conf import settings
from django.db import models
from django.db.models.fields.files import FieldFile
from django.db.models.fields.files import ImageFieldFile

from ... import log
from ...utils import path_clean
from ...utils import join_urls
from ...utils.file import unique_name_reversible
from ...storage import public_storage
from ...storage import protected_storage
from ...form import mpFileFormField
from ...form import mpImageFormField


class _mpFileAttrFieldMixin:
    """
    Additions to the model field's file attr class (which is Django File class):

        - Store unique file names to avoid collisions with uploads
        - Do not store paths in DB to decouple S3 folder location

    S3 FOLDERS MUST BE KEPT IN SYNC with any code assumptions for storage paths
    """

    def _storage_path( self, name ):
        """
        File names in the DB do NOT include a path;
        ALL paths under folder areas are built up by a model's:

            public_storage_path
            protected_storage_path

        This ensures that if folder structure changes, the
        data stored in individual items won't need to be updated.
        """
        path = getattr( self.instance, self.storage_path )

        # HACK - To handle any bad/historical data strip any leading path
        name = path_clean( name ).split('/')[-1]

        rv = join_urls( path, name )

        log.debug2("File field path %s: %s -> %s", self.instance, name, rv )
        return rv

    def _storage_name( self, name ):
        """
        If the model has name handler use it, otherwise create
        a default unique name.
        """
        name_fn = getattr( self.instance, self.storage_name, None )
        if name_fn:
            rv = name_fn( name )
        else:
            rv = unique_name_reversible( name )
            log.debug2("File field name %s: %s -> %s", self.instance, name, rv )
        return rv

    @property
    def url( self ):
        """
        Url path to resource used to access the protected content
        Add the tenant information back onto the URL.
        """
        if self.name:
            rv = self.storage.url( self._storage_path( self.name ) )
        else:
            rv = ''
        log.detail3("File field url: %s -> %s", self, rv )
        return rv

    @property
    def file_path( self ):
        """
        Return path to file for S3 or other file storage
        """
        return self._storage_path( self.name )

    def save( self, name, content, save=True ):
        """
        When saving a new upload, capture the unique filename, stripping out
        any additional information passed from the form
        """

        # Instead of using Django's geneate_filename and upload_to mechanism,
        # just get file file name from base field and add any model customization
        name = path_clean( name ).split('/')[-1]
        name = self._storage_name( name )

        # Store to file system using the tenant path if not a direct upload
        if not self.field.direct:
            full_name = self._storage_path( name )
            full_name = self.storage.save( full_name, content )
            log.debug("Saved FieldFile: %s -> %s", self.instance, full_name)

        # Set field and model with the file name
        self.name = name
        setattr( self.instance, self.field.name, name )

        # Update the filesize cache
        self._size = content.size
        self._committed = True

        log.debug2("File field save: %s, save=%s", self, save )

        # Save the object because it has changed, unless save is False
        if save:
            self.instance.save()

class _mpImageAttrPublicFile( _mpFileAttrFieldMixin, ImageFieldFile ):
    storage_path = 'public_storage_path'
    storage_name = 'public_storage_name'

class _mpFileAttrPublicFile( _mpFileAttrFieldMixin, FieldFile ):
    storage_path = 'public_storage_path'
    storage_name = 'public_storage_name'

class _mpFileAttrProtectedFile( _mpFileAttrFieldMixin, FieldFile ):
    storage_path = 'protected_storage_path'
    storage_name = 'protected_storage_name'

"""------------------------------------------------------------------
    Model file fields
    Support both public and protected files with keyword modification.
    Also supports direct widgets (widgets are selected by the form fields).
"""
class BaseFileField( models.ImageField ):
    """
    Use ImageField as common base class as it meets needs for image and file.
    """
    def __init__( self, **kwargs ):

        # Note whether field supports direct upload
        self.direct = kwargs.pop( 'direct', False ) and settings.MP_CLOUD

        # Does this field use mpFileFieldFormMixin to add metadata
        self.mpfile = kwargs.pop( 'mpfile', False )

        # Options for default rendering
        self.mpoptions = kwargs.pop( 'mpoptions', {} )

        # Set storage to class default
        kwargs['storage'] = self.storage

        super().__init__( **kwargs )

        # Add support for direct widget if needed
        if self.direct:
            self.type = 'TextField'
        else:
            self.type = super().get_internal_type()

    def formfield( self, **kwargs ):

        # Set Form field class to default for field type
        kwargs['form_class'] = self.form_field

        # S3 widget loads directly from the browser, needs to know where to send
        if self.direct:
            kwargs['direct'] = True
            kwargs['protected'] = self.is_protected
        else:
            kwargs['mpoptions'] = self.mpoptions

        return super().formfield( **kwargs )

    def get_internal_type(self):
        return self.type

    @property
    def is_protected( self ):
        return self.storage == protected_storage

class mpImageField( BaseFileField ):
    # Assume image field is public
    storage = public_storage
    attr_class = _mpImageAttrPublicFile
    form_field = mpImageFormField

class mpFileFieldProtected( BaseFileField ):
    storage = protected_storage
    attr_class = _mpFileAttrProtectedFile
    form_field = mpFileFormField

class mpFileFieldPublic( BaseFileField ):
    storage = public_storage
    attr_class = _mpFileAttrPublicFile
    form_field = mpFileFormField
