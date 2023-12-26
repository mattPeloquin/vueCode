#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Package root tasks
"""

from ..models import Package
from ..models import PackageRoot
from . import task_queryset


def package_fixup( log, sandbox, commit, limit, constraint ):
    """
    Make package and package root relationships are valid
    """
    log.info("CHECKING PACKAGES => %s, commit(%s), limit(%s), constraint(%s)", sandbox, commit, limit, constraint)

    limit_count = 0

    packages = task_queryset( Package.objects, sandbox, filter=constraint )

    for package in packages:

        roots = package.current_roots.all()
        if not roots:
            roots = PackageRoot.objects.filter( current_id=package.pk )
            if roots:
                log.debug("&nbsp;&nbsp;Not current: %s", package)

        if len( roots ) > 1:
            log.info("ERROR DATA - Multiple package roots: %s -> %s", package, roots)

        if sandbox:
            for root in roots:
                if not root.provider == sandbox.provider:
                    log.info("ERROR DATA - Package root outside provider: %s -> %s", package, sandbox.provider)

        if not package.package_root:
            if not roots:
                log.info("ERROR DATA - Package with no root package: %s", package)
                continue

            # The case of package root being out of whack can be fixed up
            root = roots[0]
            assert root

            if not package.package_root == root:
                log.info("HEAL - Package root out of whack: %s -> %s", package, root)
                if commit:
                    package.package_root = root
                    package.save()
                    log.debug("&nbsp;&nbsp;Root set complete")

        log.debug("Completed: %s", package)

        limit_count += 1
        if limit and limit_count > int(limit):
            log.info("Stopping package fixup due to limit of %s: ", limit)
            break

    log.info("PACKAGE FIXUP COMPLETE")
