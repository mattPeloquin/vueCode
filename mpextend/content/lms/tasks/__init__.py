#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Package-related tasks
"""

# Register startup singleton
from .fixup import package_fixup
from .root_cleanup import package_root_cleanup
from .leaf_cleanup import package_leaf_cleanup
from .file_cleanup import package_file_cleanup


def task_queryset( manager, sandbox, sandbox_filter='sandbox',
                   filter_value=None, filter='id' ):
    """
    Helper method for common task action of gettin a queryset of items that match
    the sandbox and constraint

    If and ID is provided, only return item if it is in the sandbox
    """
    filter_args = {}

    if sandbox:
        filter_args.update({ sandbox_filter: sandbox })

    if filter_value:
        filter_args.update({ filter: filter_value })

    rv = manager.filter( **filter_args )
    if not rv:
        log.info("NO ITEMS MATCH REQUEST => %s => %s: %s => %s: %s",
                    manager, sandbox, sandbox_filter, filter_value, filter)
    return rv
