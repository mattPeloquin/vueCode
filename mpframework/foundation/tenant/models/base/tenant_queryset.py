#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    MPF tenancy manager
"""
from mpframework.common import log
from mpframework.common.model import BaseQuerySet

from ...query_filter import tenant_filter_parse
from ...query_filter import tenant_filter_args


class TenantQuerySet( BaseQuerySet ):
    """
    Provide tenant filtering
    """

    def filter( self, *args, **kwargs ):
        return self._tenant_filter( *args, **kwargs )

    def exclude( self, *args, **kwargs ):
        kwargs.update({ '_exclude': True })
        return self._tenant_filter( *args, **kwargs )

    def get( self, *args, **kwargs ):
        """
        Use tenant filtering on a get
        Similar to Django's get, will raise DoesNotExist error if doesn't exist,
        but logs error instead of exception if MORE than one exists so things
        can move forward if there is a data issue.
        """
        qs = self._tenant_filter( *args, **kwargs )
        num = len( qs )
        if num > 0:
            if num > 1:
                log.warning("ERROR DATA - Multiple get %s: %s %s, %s -> %s",
                        self.model.__name__, args, kwargs, self.query, qs._result_cache)
                log.debug_stack()

            return qs._result_cache[0]

        raise self.model.DoesNotExist("Not found {} -> {}, {}".format(
                                           self.model.__name__, args, kwargs))

    def get_from_id( self, sandbox, id ):
        return self.get_quiet( sandbox_id=sandbox.pk, id=id )

    def _tenant_filter( self, *args, **kwargs ):
        """
        Wraps filter calls to add tenancy
        Can be called more than once for a queryset if multiple filters applied
        Is called for prefetched items, so make sure to trace actual
        SQL calls when performance tuning
        """
        negate = kwargs.pop( '_exclude', False )

        # Fixup kwargs based on optional context such as request
        # and filtering relationships to sandbox/provider
        args, kwargs = self._filter_args( *args, **kwargs )

        # Setup default Django queryset processing (queryset execution is lazy)
        clone = self._filter_or_exclude( negate, args, kwargs )

        if log.debug_on():
            log.db3("tenant_filter: %s => %s -> %s, %s", self.model.__name__,
                      str(clone.query.table_map), len(args), len(kwargs))
        return clone

    def _filter_args( self, *args, **kwargs ):
        """
        Derived queryset classes can overide default tenant processing
        """
        kwargs = tenant_filter_parse( **kwargs )
        return tenant_filter_args( self.model, *args, **kwargs )
