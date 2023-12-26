#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Remove unused package roots
"""

from ..models import PackageRoot
from . import task_queryset


def package_root_cleanup( log, sandbox, commit, limit, constraint ):
    """
    Remove package roots that are no longer in use

    Note removal will trigger removal of all packages underneath the root
    """
    log.info("CHECKING PACKAGE ROOTS => %s, commit(%s), limit(%s), constraint(%s)", sandbox, commit, limit, constraint)

    limit_count = 0

    roots = task_queryset( PackageRoot.objects, sandbox, filter_value=constraint )

    for root in roots:

        # Is this root used
        if root.lms_items.exists():
            log.debug("Root in use: %s => %s", root, list(root.lms_items.all()))
            continue

        log.info("%s %s", "CLEANING" if commit else "WOULD CLEAN", root)
        try:
            if commit:

                root.delete()

        except Exception as e:
            log.info("Exception deleting root: %s", e)

        limit_count += 1
        if limit and limit_count >= int(limit):
            log.info("Stopping due to limit of %s: ", limit)
            break

    log.info("PACKAGE ROOT CLEANUP COMPLETE")
