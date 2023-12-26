#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Optimized choice field

    Designed to support rendering widgets with values_list querysets.
    This can make DB query more efficient, but most important,
    saves on object creation to populate widget with many items.
"""
from django import forms


class TupleQuerysetValuesMixin:

    def prepare_value( self, obj ):
        # HACK - Django calls this on render to create select items, and on save to get
        # values, with difference being an iterable. Since tuple is passed by values_list
        # optmization, assume list vs. tuple here for the 2 scenarios
        rv = obj
        if isinstance( obj, tuple ):
            rv = obj[0]
        elif hasattr( obj, '__iter__' ) and not hasattr( obj, '_meta' ):
            rv = [ super(TupleQuerysetValuesMixin, self).prepare_value(v) for v in obj ]
        return rv

    def label_from_instance( self, obj ):
        return obj and obj[1]


class mpModelMultipleChoiceField( TupleQuerysetValuesMixin, forms.ModelMultipleChoiceField ):
    """
    Supports optimized horizontal_filters
    """

    def result_queryset( self, value ):
        # This must be overridden in specialized classes to return
        # queryset with correct model types
        return

    def _check_values( self, value ):
        # HACK - override the multiple choice field value checking to return
        # a new query set of the selected items
        return self.result_queryset( value )
