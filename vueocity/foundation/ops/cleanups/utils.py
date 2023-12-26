#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Ops cleanup task views
"""

from mpframework.common import log


class _Logger:
    """
    Support LIMITED logging to log and returning message string for page output
    """
    def __init__( self ):
        self.output = []

    def info( self, *args, **kwargs ):
        log.info( *args, **kwargs )
        self.output.append( str(args[0]) % args[1:] )

    def debug( self, *args, **kwargs ):
        self.output.append( log.debug( *args, **kwargs ) )


def cleanup_shell( fn, user, commit, limit, constraint ):
    """
    For one-time tasks such as non-reversible programmatic data migration,
    add code with this decorator
    """
    log.debug("%s -- RUNNING TASK! commit=%s, limit=%s", user, commit, limit)
    logger = _Logger()
    try:
        # Determine if the operation is constrained to sandbox or is system wide
        sandbox = None if user.logged_into_root else user.sandbox

        # Call the task function
        fn( logger, sandbox, commit, limit, constraint )

    except Exception as e:
        log.exception("TASK: %s => %s", user, e)
        logger.info("EXCEPTION: %s", e)

    return logger.output
