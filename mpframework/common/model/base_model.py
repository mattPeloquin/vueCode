#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Base model for most models in framework
"""
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from .. import log
from ..utils import now
from ..utils import timedelta_minutes
from ..utils import json_dump
from .fields import mpDateTimeField


class BaseModel( models.Model ):
    """
    Handle generic shared behavior across all models:
        - Basic date tracking of object creation and change
        - Support for conversion to JSON

    ordering is not specified in BaseModel (or MPF models in general)
    to avoid adding ORDER_BY to all queries when not needed.
    """

    # Keep track of modification
    # Accept blanks here to make loading test fixtures easier and because these
    # are modified programatically
    # Index as needed in derived classes
    hist_created = mpDateTimeField( default=now, verbose_name=u"Created" )
    hist_modified = mpDateTimeField( default=now, verbose_name=u"Modified" )

    # Class-level access to content type, to support filtering on classes
    # HACK - stash content type at the class level
    @classmethod
    def get_django_ctype( cls ):
        if not cls.__django_ctype:
            cls.__django_ctype = ContentType.objects.get_for_model( cls )
        return cls.__django_ctype
    __django_ctype = None

    class Meta:
        abstract = True

    def __init__( self, *args, **kwargs ):
        super().__init__( *args, **kwargs )
        self._log_instance("Init")

    def _log_instance( self, message ):
        log.debug_on() and log.detail2("%s: %s (%s)", message, self.unique_key, id(self))

    def save( self, *args, **kwargs ):
        self._log_instance("Saving")
        modify_time = kwargs.pop('modify_time', True)

        # Capture time info
        if modify_time:
            time_now = now()
            self.hist_modified = time_now
            if not self.hist_created:
                self.hist_created = time_now

        super().save( *args, **kwargs )

    def _save_table( self, *args, **kwargs ):
        """
        QS db property logging isn't used for many saves, so add logging here
        """
        log.debug2("DB SAVE %s -> %s", self.unique_key, id(self))
        return super()._save_table( *args, **kwargs )

    def update( self, **kwargs ):
        """
        Convenience update based on dict of attributes
        """
        for attr, value in kwargs.items():
            setattr( self, attr, value )

    @property
    def unique_key( self ):
        """
        Returns a unique string shared by instances of the model
        """
        return self.__class__.__name__ + str( self.pk )

    @property
    def type_name( self ):
        """
        Overridable description of class type for use in UI
        """
        return self.__class__.__name__

    @property
    def downcast_model( self ):
        """
        Overridden in Concrete mixin to provide for efficient downcasts
        """
        return self

    @property
    def wraps( self ):
        """
        Standardized, overridable access to underlying model. This is normally
        itself, but some models may wrap others.
        """
        return self

    def json( self, extra_info=None, **kwargs ):
        """
        Provide json string of data defined by model's info property plus any extra_info
        """
        values = self.dict
        if extra_info:
            values.update( extra_info )
        return json_dump( values, **kwargs )

    @property
    def dict( self ):
        """
        Overridable representation of object as dict intended to be converted to json
        """
        return {
            'id': self.pk,
            }

    @property
    def dev_mode( self ):
        return settings.DEBUG

    def created_in_minutes( self, minutes ):
        return minutes > timedelta_minutes( now() - self.hist_created ) if self.hist_created else False

    def modified_in_minutes( self, minutes ):
        return minutes > timedelta_minutes( now() - self.hist_modified ) if self.hist_modified else False
