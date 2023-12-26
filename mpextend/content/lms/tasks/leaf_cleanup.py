#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Package leaf cleanup
"""

from ..models import Package
from . import task_queryset


def package_leaf_cleanup( log, sandbox, commit, limit, constraint ):
    """
    Remove package leaves (and their s3 resources) that are:

        - Not current for a package root and not used
          (happens frequently when staff upgrades version for all users)

        - Orphaned from a package root and no users (bad data condition)

    A grace period is used to not remove any recently modified package
    """
    log.info("CHECKING PACKAGE LEAVES => %s, commit(%s), limit(%s), constraint(%s)", sandbox, commit, limit, constraint)

    limit_count = 0

    packages = task_queryset( Package.objects, sandbox, filter_value=constraint )

    for package in packages:

        # Is this package is the current package for any root?
        if package.current_roots.exists():
            log.debug("Current: %s => %s", package, list(package.current_roots.all()))
            continue

        # Is this package used by any students?
        if package.user_items.exists():
            log.debug("Not current, but in use: %s", package)
            if not package.package_root:
                log.info("Warning, package in use with no root, run fixup: %s", package)
            continue

        log.info("%s %s", "CLEANING" if commit else "WOULD CLEAN", package)
        try:
            if commit:

                package.delete()

        except Exception as e:
            log.info("Exception deleting package: %s", e)

        limit_count += 1
        if limit and limit_count >= int(limit):
            log.info("Stopping due to limit of %s: ", limit)
            break

    log.info("PACKAGE LEAF CLEANUP COMPLETE")

