#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Admin large table admin performance mixin (mySQL optimizations)

    Pagination with ordering can cause larger table queries to take 10s of seconds
    due to MySql's crazy lack of late row lookup optimization.

    Instead of displaying pagination for all the rows, show only a sample.
    UX assumption is user will always need to search/filter down the large set
    to find what they are looking for, so a sample normally isn't a major issue...
"""
from django.conf import settings
from django.db import connection
from django.forms.models import BaseModelFormSet

from . import BaseChangeList


_MAX_COUNT_MULTIPLIER = 8


class AdminLargeMixin:
    """
    The mixin class must appear before the main admin class derived from ModelAdmin
    """

    def __init__( self, *args, **kwargs ):
        self.mp_sample = None
        super().__init__( *args, **kwargs )

    def get_changelist( self, request, **kwargs ):
        return _LargeChangeList

    def get_changelist_formset( self, request, **kwargs ):
        return super().get_changelist_formset( request, formset=_LargeModelFormSet )

class _LargeChangeList( BaseChangeList ):

    def get_queryset( self, request ):
        """
        Restructure the query as an unordered sample of IDs, which are then
        loaded and managed with ordering.
        """
        qs = super().get_queryset( request )
        self.orig_qs = qs.all()
        self.mp_sample = self.list_per_page * _MAX_COUNT_MULTIPLIER

        # Get a block of ids items that match the search criteria
        id_qs = qs.values_list( 'id', flat=True )[ :self.mp_sample ]

        # HACK - potential mySQL optimization
        sql, params = id_qs.query.sql_with_params()
        if settings.MP_CLOUD:
            sql = sql.replace( 'INNER JOIN', 'STRAIGHT_JOIN' )

        with connection.cursor() as cursor:
            cursor.execute( sql, params )
            ids = [ result[0] for result in cursor.fetchall() ]

        # Create a new queryset from the subset
        if ids:
            wrap_qs = self.model.objects.filter( id__in=ids )

            # Add original select related and ordering
            wrap_qs.query.select_related = qs.query.select_related
            ordering = self.get_ordering( request, qs )
            wrap_qs = wrap_qs.order_by( *ordering )

            # Prevent DB count on the IDs found
            wrap_qs.count = lambda: len( ids )

            qs = wrap_qs
        else:
            qs = self.model.objects.none()

        return qs

    def get_results( self, request ):
        """
        Fixup count to show the actual number of matched items, even if limited
        FUTURE - consider time cached window for counts, as they can be
        expensive to do full count to display totals for each screen.
        """
        super().get_results( request )

        # The result count is set to the sample size that was returned;
        # ideally would run count for original query if sample didn't capture
        # all results, but that can trigger very expensive scanning
        # So compromise with indicator in UI that not all results are shown
        if self.mp_sample and not ( self.result_count < self.mp_sample ):
            self.result_incomplete = True


class _LargeModelFormSet( BaseModelFormSet ):
    """
    HACK - Override Django formset, which sneaks in an ordering on a queryset
    call during FormSet creation to size the FormSet
    """
    def get_queryset( self ):
        if not hasattr( self, '_queryset' ):
            if self.queryset is not None:
                qs = self.queryset
            else:
                qs = self.model._default_manager.get_queryset()
            self._queryset = qs
        return self._queryset
