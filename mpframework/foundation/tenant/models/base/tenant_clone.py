#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared code used for cloning across tenancy base classes
"""
from django.conf import settings
from django.db import transaction

from mpframework.common import log
from mpframework.common.logging.timing import mpTiming
from mpframework.common.aws import s3
from mpframework.common.tasks import mp_async
from mpframework.common.tasks import run_queue_function
from mpframework.common.model.fields.files import BaseFileField
from mpframework.common.model.utils import data_fields

from .tenant_model import TenantBaseMixin


class TenantCloneMixin( TenantBaseMixin ):
    """
    Models that use the TenantManager need to include this mixin.
    """

    # Data-driven mechanism used in cloning (see below)
    _clone_fixups = ()

    @transaction.atomic
    def clone( self, **kwargs ):
        """
        The object that calls this is the SOURCE used to create a new
        TARGET object of the same type, with cloned data/resources.
        """
        full = kwargs.pop( 'full_clone', True )
        log.info2("CLONING %s, full: %s", self, full)

        attrs = self._clone_attrs( full, **kwargs )
        log.debug("New attributes: %s", attrs)

        rv = self.__class__.objects.create_obj( **attrs )
        if full:
            rv._clone_resources( self )

        return rv

    def _clone_attrs( self, full, **kwargs ):
        """
        If _tenancy_type value in kwargs is...

          - Set to an object, cloning will set tenancy value to that object
          - True, object will be copied within its existing tenancy (default)
          - None, nothing is assumed about setting up tenancy; provider/sandbox
            fields need to be set manually.

        If the model has _clone_xxx class parameters, these are used to fix
        up the clone with relationships and values that cannot be
        directly copied from the source -- but only if _tenancy_type is present
        and matches the cloned object's tenancy.
        """
        attrs = {}

        # These are sort of reserved words; don't want a model field with these names
        exclude_relationships = kwargs.pop( 'exclude_relationships', True )
        includes = kwargs.pop( '_includes_', [] )
        excludes = kwargs.pop( '_excludes_', [] )

        # Clone's creation date should be from cloning
        excludes.append('hist_created')

        # Copy values from source to new clone
        for field in data_fields( self, exclude_relationships, includes, excludes ):
            name = field.name
            value = getattr( self, name )

            if isinstance( field, BaseFileField ):
                value = value.name

            attrs[ name ] = value

        # Setup tenancy, if one is going to be used
        tenancy = kwargs.pop( self._tenancy_type, True )
        if tenancy is True:
            tenancy = getattr( self, self._tenancy_type )
        if tenancy:
            attrs[ self._tenancy_type ] = tenancy

            # Do any fixups - items with matching names must already exist in target
            for typ, fixup in self._clone_fixups:

                # Make foreign key point to item in this tenancy that matches name
                if typ == 'FK':
                    model, fk, name = fixup
                    value = getattr( getattr( self, fk ), name, None )
                    fk_obj = model.objects.get_quiet(**{
                                   self._tenancy_type: tenancy,
                                   name: value })
                    if fk_obj:
                        attrs[ fk ] = fk_obj

                # If unique string field exists, add count to string
                elif typ == 'STRING':
                    value = attrs[ fixup ]
                    existing = self.__class__.objects.filter(**{
                                   self._tenancy_type: tenancy,
                                   fixup: value }).count()
                    if existing:
                        attrs[ fixup ] = "{}-{}".format( value, existing + 1 )

        # Apply explicit values that were passed in
        attrs.update( kwargs )
        return attrs

    def clone_fixup( self, source_sandbox ):
        """
        Allows for any additional fixup based on the original sandbox relationships.
        Typically called on TARGET item AFTER cloning from source has been done
        on all related items, to ensure efficient updates (see Tree).
        """
        pass

    def _clone_resources( self, obj ):
        """
        Setup async job to copy resources FROM SOURCE obj TO THIS TARGET object
        for all field types that have external resources.
        ASSUMES MODELS ARE SAME TYPE AND FIELD DATA IS ALREADY SETUP.
        Only items with an entry in both target and source will be copied.
        """
        try:
            file_data = self._clone_file_data( obj )
            if file_data:
                log.debug("S3 file copy task: %s -> %s", obj, file_data)
                # Run task in its own group based on the target object,
                # which means these jobs will each be their own group and not
                # block on message visibility of other groups.
                # FUTURE SCALE - if having clone tasks for all objects take
                # over queue messages is problematic, group them by target
                # or source sandbox
                group = obj

                run_queue_function( _copy_s3_files, group, my_priority='HS',
                            file_data=file_data )
        except Exception:
            log.exception("Problem setting clone resource: %s", self)
            if settings.MP_TESTING:
                raise

    def _clone_file_data( self, obj ):
        """
        Overridable logic for setting up S3 file copy job
        """
        rv = {}
        for field in obj._meta.get_fields():
            if not isinstance( field, BaseFileField ):
                continue
            try:
                source = getattr( obj, field.name )
                target = getattr( self, field.name )

                # Only send valid files (will have names, unlike folders)
                if target.name and source.name:
                    rv[ field.name ] = {
                        'bucket': 'protected' if field.is_protected else 'public',
                        'source': source.file_path,
                        'target': target.file_path,
                        }
                    log.debug("Clone resources data: %s -> %s, %s",
                                field.name, self, rv[ field.name ])

            except Exception:
                log.exception("Problem clone file field: %s -> %s", self, field)
                if settings.MP_TESTING:
                    raise
        return rv

@mp_async
def _copy_s3_files( **kwargs ):
    """
    Execute the copy of file resources
    This is a module function since it needs to be imported by spooler
    """
    data = kwargs['file_data']
    if not data:
        raise Exception("S3 Resource copy with no file data")
    t = mpTiming()

    for name, info in data.items():
        try:
            bucket = info['bucket']
            source = info['source']
            target = info['target']
            log.debug("%s Copying field resources: %s, %s, %s -> %s",
                         t, name, bucket, source, target)

            s3.copy_file( bucket, source, target )

        except Exception:
            log.exception("S3 Resource copy error: %s", kwargs)

    log.info("<= %s S3 COPY complete: %s items", t, len(data.items()))
