#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Concrete model polymorphism.

    Django maintains "ctype"/"contenttype" table with model names - the names in
    django_content_type DB tabled are lowercase model name strings.

    MODEL NAME CHANGES REQUIRE UPDATE of ContentType table to
    reflect the new ctype name (or use temporary _CTYPE_MIGRATION).
    Servers must be restarted if content types change due to process caching.
"""
from copy import copy
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from .. import log
from .utils import field_names


# HACK - support as-needed temp cutover of ctype name changes by encoding mapping
# of new class name to old ctype name until the django content type table is updated
_CTYPE_MIGRATION = {
    }


class ConcreteBaseMixin( models.Model ):
    """
    Mixin to add downcasting to concrete inheritance

    The semantics around managing _django_ctype between base class and
    specializations assume:

     - The base class is never instantiated, only specializations
     - Only 1 level of inheritance is checked

    Polymorphic querysets of sub classes should use InheritanceManager instead.
    """

    """--------------------------------------------------------------------
        Polymorphic support for optimized conversion of items to specialized
        sub-classes. Concrete model inheritances uses a base table for the base
        class and join tables for the specialized classes.

        Django stores class names for models in the ContentTypes table.

        Models composing this mixin use _django_ctype in base class table that
        keeps track of the sub-class type the base table row corresponds to.

        Django supports querying a baseobject with the name of a specialization
        to cast it, but that just does a query on the specialized table,
        which would need to be done on all if specialized type is unknown.
    """

    # DB Link from specialization type to base class type
    # Nulls support test fixture and other data setup
    _django_ctype = models.ForeignKey( ContentType, models.SET_NULL,
                null=True, blank=True, db_column='_content_type_id' )

    class Meta:
        abstract = True

    def save( self, *args, **kwargs ):
        """
        Make sure new objects have their specialized type saved
        """
        if not self._django_ctype:
            self._django_ctype = ContentType.objects.get_for_model( self.__class__ )
        super().save( *args, **kwargs )

    def downcast_call( self, fn_name, *args, **kwargs ):
        """
        Call special downcast methods WITHOUT hitting DB

        DOWNCAST METHODS ARE READ ONLY

        HACK - specialized methods are separated from the base method and found
        by naming convention for functions in specialized classes:

            def method_Class( self )

        HACK - the base model is shallow copied and its class set to the
        downcast model to allow the specialized method to be called unbound.
        """
        model_class = self.downcast_type.model_class()
        if model_class:
            override_name = '_'.join([ fn_name, model_class.__name__ ])
            fn = getattr( model_class, override_name, None )
            if fn:
                log.detail3("Downcast call (no DB): %s => %s -> %s", override_name, self, model_class)
                down_model = copy( self )
                down_model.__class__ = model_class
                return fn( down_model, *args, **kwargs )

        log.detail3("Downcast call (no DB): %s_Base => %s -> %s", fn_name, self, model_class)
        fn = getattr( self, fn_name )
        return fn( *args, **kwargs )

    @property
    def downcast_type( self ):
        """
        Return the downcast content type of this model.

        Only hits DB if healing is needed. To handle test data and self-healing,
        when content type is not set it will be set from current type.

        BE CAREFUL MANAGING CHANGES to ctype names in production if multiple
        versions of code with different ctype names need to overlap for a period.
        """

        # Heal an empty content id
        if not self._django_ctype_id:
            if settings.MP_IS_DJ_SERVER:
                log.detail3("ConcreteBase fixing up content fixture: %s", self)
            else:
                log.info("HEAL - ConcreteBaseMixin django content type fixup: %s", self)

            # Find name of pointer to base class either through class name or by convention
            base_ptr_name = self._meta.model_name + "_ptr"
            for field_name in field_names( self ):
                if field_name.startswith('base') and field_name.endswith('_ptr'):
                    base_ptr_name = field_name
                    break

            # Then find the content type that matches the specialized class row
            # HACK - Go through all content types for the app and try to lookup
            # ID in any classes that have a pointer to the concrete base class
            for ctype in ContentType.objects.filter( app_label=self._meta.app_label ):
                klass = ctype.model_class()
                if klass and base_ptr_name in field_names( klass ):
                    sub_class = klass.objects.filter( id=self.pk )
                    if sub_class:
                        log.detail3("ConcreteBase found specialized class: %s -> %s, %s",
                                    self, sub_class, ctype)
                        self._django_ctype = ctype
                        self.save( modify_time=False, invalidate=False )
                        break
            assert self._django_ctype

        # Normally provide content type from Django cached call
        rv = ContentType.objects.get_for_id( self._django_ctype_id )

        # HACK - check for temporary migration where specialized model name has changed
        # IF there is a problem, fix up with new ContentType
        if _CTYPE_MIGRATION:
            if not rv.model_class():
                rv = ContentType.objects.get_by_natural_key( self._meta.app_label,
                        _CTYPE_MIGRATION[ self._django_ctype_id ] )
                log.debug("ctype fixup: %s -> %s", self, rv)

        return rv

    @property
    def downcast_model_name( self ):
        return self.downcast_type.model

    @property
    def downcast_model( self ):
        """
        Return downcast model for a baseitem -- HITS DB IF DOWNCAST IS NEEDED
        Consider using InheritanceManager to get querysets of sub classes instead
        """
        model_class = self.downcast_type.model_class()

        if not model_class:
            log.warning("MISSING CONTENT TYPE: %s, %s -> %s, %s", self,
                    self.downcast_type, model_class, self._django_ctype)
            return self

        if model_class == self.__class__:
            log.debug2("Skipping downcast: %s -> %s", self, model_class)
            return self

        log.debug2("Downcast model (db hit): %s -> %s", self, model_class)
        return model_class.objects.get( id=self.pk )
