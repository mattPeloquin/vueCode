#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Mesa Platform Framework (MPF)
"""

"""-----------------------------------------------------------------
    Provide a load-time mechanism apart from Django settings to support
    aggregation of return values from groups of multiple functions
    across MPF area boundaries.
    _mpf_function_groups holds LISTS of functions, that apps can add
    as they are loading, with functions that returns lists
    which will be combined when mpf_function_group_call is called.
"""
_mpf_function_groups = {}

def mpf_function_group_register( name, item_fn ):
    item_fns = _mpf_function_groups.get( name, [] )
    item_fns.append( item_fn )
    _mpf_function_groups[ name ] = item_fns

def mpf_function_group_call( name ):
    item_fns = _mpf_function_groups.get( name, [] )
    rv = []
    for item_fn in item_fns:
        rv.extend( item_fn() )
    return rv
