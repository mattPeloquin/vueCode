#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Support for base class declaration of select_related and prefetch_related
"""

from .. import log


def add_related_fields( qs, model, **kwargs ):
    """
    Look for tuples on a model defining related fields to add to a queryset

    This behavior is on by default, but can be overridden in get_queryset

    Each model can define regular and admin versions of select_related
    and prefetch_related class values. Admin values will default to
    the regular values if not present, but not vice versa.
    """
    orig_qs = qs

    select = kwargs.pop( 'select', True )
    prefetch = kwargs.pop( 'prefetch', True )
    group = kwargs.pop( 'group', None )

    if select:
        select_fields = _get_related_fields( model, 'select_related', group )
        if select_fields:
            qs = qs.select_related( *select_fields )

    if prefetch:
        prefetch_fields = _get_related_fields( model, 'prefetch_related', group )
        if prefetch_fields:
            qs = qs.prefetch_related( *prefetch_fields )

    if log.debug_on():
        if (select and select_fields) or (prefetch and prefetch_fields):
            log.db2("add_related_fields %s ORIGINAL: %s", group if group else "",
                            str(orig_qs.query).split('FROM')[1:])
            select and select_fields and log.db3("add_related_fields SELECT: %s => %s",
                                                     model.__name__, select_fields)
            prefetch and prefetch_fields and log.db3("add_related_fields PREFETCH: %s => %s",
                                                         model.__name__, prefetch_fields)

    return qs


def _get_related_fields( model, name, group ):
    """
    Try group name first if requested, then try regular
    """
    rv = None
    if group:
        rv = getattr( model, '%s_%s' % (name, group), None)
    if rv is None:
        rv = getattr( model, name, None)
    return rv
