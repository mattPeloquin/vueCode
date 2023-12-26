#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    One to one field extension
    Supports MPF patterns for downstream apps to link to upstream apps
    through 1:1 proxy models.

    PORTIONS ADAPTED FROM OPEN SOURCE:
        https://github.com/skorokithakis/django-annoying/blob/master/annoying/fields.py
"""
from django.db import models
from django.db import transaction
from django.db.utils import IntegrityError
from django.db.models.fields.related_descriptors import ReverseOneToOneDescriptor

from ... import log


class mpOneToOneField( models.OneToOneField ):
    """
    Create a 1:1 model field that:
      - Has option to return None instead of exception if no record
      - Otherwise automatically creates new record
    Automatic creation only works if the default instance manager can
    create an object with only upstream instance.
    """

    def __init__( self, *args, **kwargs ):
        self.allow_null = kwargs.pop( 'allow_null', False )
        super().__init__( *args, **kwargs )

    def contribute_to_related_class( self, cls, related ):
        setattr( cls, related.get_accessor_name(),
                    _ReverseOneToOneDescriptor( related, self.allow_null ) )

class _ReverseOneToOneDescriptor( ReverseOneToOneDescriptor ):
    """
    Django model field descriptors hold logic for model key connections.
    """

    def __init__( self, related, allow_null=False ):
        self.allow_null = allow_null
        super().__init__( related )

    def __get__( self, instance, instance_type=None ):
        """
        Implement MPF functionality with override the default reverse 1:1 get.
        """
        model = getattr( self.related, 'related_model', self.related.model )
        try:
            # If record already exists, nothing to do
            return super().__get__( instance, instance_type )
        except model.DoesNotExist:
            if self.allow_null:
                return
        try:
            with transaction.atomic():
                obj, _ = model.objects.get_or_create(**{
                            self.related.field.name: instance })
                # Update Django's cache to avoid initial calls returning different objects
                import django
                self.related.set_cached_value( instance, obj )
                self.related.field.set_cached_value( obj, instance )
                return obj

        except IntegrityError as e:
            # Can fail between __get__ and the get_or_create
            # FUTURE - if conflicts happen often, reduce creation contention
            log.info2("RACE creating reverse one-to-one: %s -> %s",
                        instance, e)
            # Return the object that was just created
            return super().__get__( instance, instance_type )
