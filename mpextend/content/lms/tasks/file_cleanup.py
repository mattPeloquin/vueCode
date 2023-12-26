#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Package root tasks
"""


def package_file_cleanup( log, sandbox, commit, limit, constraint ):
    """
    FUTURE -- scan AWS for orphan files/folders with no package leaf
    """

    if sandbox:
        log.info("PACKAGE FILE CLEANUP CAN ONLY BE RUN FROM ROOT SANDBOX!" )
        return

    log.info("CHECKING PACKAGE FILES => commit(%s), limit(%s)", commit, limit)



    log.info("CHECKING FILES COMPLETE!")
