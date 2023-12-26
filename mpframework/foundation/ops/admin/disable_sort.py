#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    MONKEY PATCH Django to provide easy disable of change list sorting
    by overriding results headers.

    This is necessary because the sorting HTML is created in the
    results_header HTML tag, based on the attr of the list_display
    fields -- so unless a field override is created for each
    item to disable admin_order_field there is no way to easily
    set columns in a changelist to non-sorting, even with the
    BaseChangeList override.

    FUTURE DJ3 - there is patch for Django not released yet that adds
    explicit column sorting as a feature
"""
from django.contrib.admin.templatetags import admin_list
from django.contrib.admin.templatetags.admin_list import result_headers


orig_result_headers = result_headers

def result_headers( cl ):
    """
    HACK - implement disable of sorting by overriding where Django provides info
    for creating HTML in changelist headers
    """
    no_sorting_fields = getattr( cl.model_admin, 'list_display_not_sortable', () )

    # Result headers aren't tied to fields, so need to get indices of items
    # in the list that match disable
    disable_indices = []
    for i, field_name in enumerate( cl.list_display ):
        if field_name in no_sorting_fields:
            disable_indices.append( i )

    # Update any explicitly named fields to ensure they won't sort
    for i, header in enumerate( orig_result_headers( cl ) ):
        if i in disable_indices:
            header['sortable'] = False
        yield header

admin_list.result_headers = result_headers
