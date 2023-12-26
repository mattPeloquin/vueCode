#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Admin filter controls
"""
from django.contrib.admin import SimpleListFilter
from django.contrib.admin import FieldListFilter

from .. import log
from ..utils import safe_int
from ..utils.strings import safe_unicode
from ..model.related import add_related_fields


def filter_title( title ):
    """
    Change the name of an admin filter group
    Use ('xyz', filter_title('Custom XYZ')) in place of 'xyz' in list_filter
    """
    class CustomTitleFilter( FieldListFilter ):
        def __new__( cls, *args, **kwargs ):
            instance = FieldListFilter.create( *args, **kwargs )
            instance.title = title
            return instance
    return CustomTitleFilter


class mpListFilter( SimpleListFilter ):
    """
    Default and base class for all MPF admin filters
     - Defaults to tennancy aware queryset
     - Makes default list filters support data-driven options
     - Unfiltered all is explicit state to better support...
     - ...other default admin filters like hiding active items

    To use with basic lookups, call mpListFilter.new() to create class
    for inclusion in list_filter.
    To customize lookups define new class and override lookups and queryset.
    """
    model = None

    @staticmethod
    def new( filter_model, filter_title, relationship, **kwargs ):
        """
        Easy factory method to define filters
        """
        parameter = kwargs.pop('parameter', None)

        class _NewFilter( mpListFilter ):
            model = filter_model
            title = filter_title
            id_relationship = relationship
            parameter_name = parameter if parameter else title.replace(' ', '').lower()
            lookup_kwargs = kwargs

        return _NewFilter

    def __init__( self, request, params, model, model_admin ):
        """
        Stash model_admin options
        """
        options = getattr( model_admin, 'list_filter_options', {} )
        self.options = options.get( self.__class__.__name__, {} )
        super().__init__( request, params, model, model_admin )

    def queryset( self, request, qs ):
        """
        Reduce the queryset based on filter relationship
        The queryset should already be modified for tenancy
        """
        if self.value() is None:
            return
        selection = safe_int( self.value() )
        if selection:
            return qs.filter( **{
                 self.id_relationship: selection,
                 })

    def value( self ):
        """
        Adjust value to match default if needed
        """
        return super().value() or self.options.get('default')

    def lookups( self, request, model_admin ):
        """
        Defaults to lookup of all items based on tenancy.
        Must override for other cases.
        """
        qs = self.model.objects.filter( request=request, **self.lookup_kwargs )

        # Add admin select related fields
        qs = add_related_fields( qs, self.model, group='admin' )

        # Return the lookup id/name to populate the filter selection
        items = list( qs )
        log.detail3("Adding admin filter values: %s -> %s", self.model, items)
        return [ ( item.pk, str(item) ) for item in items ]

    def choices( self, changelist ):
        """
        Make the filter dropdown honor any defaults
        """
        if not self.options.get('hide_all'):
            yield {
                'selected': self.value() is None,
                'query_string': changelist.get_query_string({ self.parameter_name: 'all' }),
                'display': u"All",
                }
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == safe_unicode( lookup ),
                'query_string': changelist.get_query_string({ self.parameter_name: lookup }),
                'display': title,
                }
